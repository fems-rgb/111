"""线性预测与成本日桶持久化（Phase B）

设计：
- 热路径（cost_tracker）只累内存日桶，本模块提供低频 flush 到 cost_daily 表；
- linear_forecast 是最小的一维最小二乘外推，三类预测（成本 / 任务 ETA / 学习进度）
  都在它之上做封装，数据不足时统一返回 {"status": "insufficient"} 而非硬造结论；
- 所有函数只读或幂等写库，失败由调用方兜底，不影响主业务。
"""
import logging
import time
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

_FLUSH_MIN_INTERVAL = 60.0   # 距上次写库至少间隔（秒），符合「低频镜像」惯例
_last_flush_at = 0.0
_MAX_ETA_SECONDS = 6 * 3600  # ETA 上限兜底：早期 percent 很小时不外推出离谱数字


# ════════════════ cost_daily 落库 ════════════════

async def flush_cost_daily(db: AsyncSession) -> bool:
    """把内存日桶镜像到 cost_daily（有变更且距上次 >=60s 才写）；返回是否执行了写入"""
    global _last_flush_at
    # 注意：包 app.observability 的 __init__ 把名字 cost_tracker 遮蔽成了实例，
    # 这里要的是模块级日桶函数，必须从子模块直接导入
    from app.observability.cost_tracker import daily_dirty, daily_snapshot, mark_daily_flushed
    from app.database.models import CostDaily

    if not daily_dirty():
        return False
    now = time.time()
    if now - _last_flush_at < _FLUSH_MIN_INTERVAL:
        return False
    _last_flush_at = now

    bucket = daily_snapshot()
    for day, v in bucket.items():
        row = (await db.execute(select(CostDaily).where(CostDaily.day == day))).scalar_one_or_none()
        if row is None:
            db.add(CostDaily(day=day, cost_yuan=round(v["cost"], 6), calls=v["calls"]))
        else:
            row.cost_yuan = round(v["cost"], 6)
            row.calls = v["calls"]
    await db.commit()
    mark_daily_flushed()
    logger.debug("[prediction] cost_daily flush %s days", len(bucket))
    return True


async def cost_history(db: AsyncSession, days: int = 30) -> list[dict]:
    """近 N 天日成本：DB 历史 + 今日内存桶覆盖，按日期升序 [{day, cost_yuan, calls}]"""
    from app.database.models import CostDaily
    from app.observability.cost_tracker import daily_snapshot

    since = (date.today() - timedelta(days=days - 1)).isoformat()
    rows = (await db.execute(
        select(CostDaily).where(CostDaily.day >= since).order_by(CostDaily.day)
    )).scalars().all()
    merged = {r.day: {"day": r.day, "cost_yuan": round(r.cost_yuan, 4), "calls": r.calls} for r in rows}
    for day, v in daily_snapshot().items():
        if day >= since:
            merged[day] = {"day": day, "cost_yuan": round(v["cost"], 4), "calls": v["calls"]}
    return [merged[d] for d in sorted(merged)]


# ════════════════ 一维最小二乘外推 ════════════════

def linear_forecast(series: list[float]) -> dict:
    """对等间隔序列做最小二乘线性拟合，外推下一期。

    返回 {status, slope, intercept, predicted, confidence(R²), n}；
    n < 3 或序列全零时 status=insufficient。
    """
    n = len(series)
    if n < 3:
        return {"status": "insufficient", "n": n, "reason": "数据不足（少于 3 个采样点）"}
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(series) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return {"status": "insufficient", "n": n, "reason": "采样点无跨度"}
    sxy = sum((x - mx) * (series[i] - my) for i, x in enumerate(xs))
    slope = sxy / sxx
    intercept = my - slope * mx
    syy = sum((y - my) ** 2 for y in series)
    ssr = sum((series[i] - (slope * x + intercept)) ** 2 for i, x in enumerate(xs))
    confidence = 1.0 - (ssr / syy) if syy > 0 else 1.0
    predicted = slope * n + intercept
    return {
        "status": "ok",
        "n": n,
        "slope": round(slope, 6),
        "intercept": round(intercept, 6),
        "predicted": round(max(predicted, 0.0), 6),
        "confidence": round(max(min(confidence, 1.0), 0.0), 3),
    }


# ════════════════ 三类预测封装 ════════════════

def predict_cost(history: list[dict]) -> dict:
    """按日成本序列外推「本月剩余天数还会花多少」与「几天后触阈」。

    history: cost_history 的输出（升序）。数据 <3 天返回 insufficient。
    """
    series = [h["cost_yuan"] for h in history]
    fc = linear_forecast(series)
    today = date.today()
    first_next = (today.replace(day=1) + timedelta(days=32)).replace(day=1)   # 下月 1 号
    days_left = (first_next - today).days          # 含今天的本月剩余天数
    month_prefix = today.strftime("%Y-%m")
    month_spend = round(sum(h["cost_yuan"] for h in history
                            if h["day"].startswith(month_prefix)), 4)   # 本月已花
    threshold = settings.COST_ALERT_THRESHOLD_YUAN
    out = {"status": fc["status"], "month_spend_yuan": month_spend,
           "threshold_yuan": threshold, "daily_avg_yuan": round(sum(series) / max(len(series), 1), 4)}
    if fc["status"] != "ok":
        return out
    # 逐日外推剩余天数（负斜率按 0 处理）
    per_day = max(fc["slope"], 0.0)
    out["predicted_daily_yuan"] = round(fc["predicted"], 4)
    out["forecast_month_total_yuan"] = round(month_spend + per_day * days_left, 4)
    out["confidence"] = fc["confidence"]
    cum = month_spend
    exceed_in_days = None
    if cum >= threshold:
        exceed_in_days = 0
    else:
        for d in range(1, 61):   # 最多展望 60 天
            cum += per_day
            if cum >= threshold:
                exceed_in_days = d
                break
    out["exceed_threshold_in_days"] = exceed_in_days
    out["will_exceed_threshold"] = exceed_in_days is not None
    return out


def eta_from_progress(percent: float, elapsed_seconds: float) -> float | None:
    """按已完成比例线性估剩余秒数；数据不可信时返回 None"""
    if percent is None or percent <= 0 or elapsed_seconds is None or elapsed_seconds <= 0:
        return None
    if percent >= 100:
        return 0.0
    eta = elapsed_seconds * (100 - percent) / percent
    return round(min(eta, _MAX_ETA_SECONDS), 1)


def eta_generation(job_view: dict) -> float | None:
    """generate deck 异步作业：created_at（epoch 秒）+ percent 估剩余"""
    started = job_view.get("created_at")
    if isinstance(started, datetime):
        started = _as_epoch(started)
    if not started:
        return None
    return eta_from_progress(job_view.get("percent") or 0, time.time() - float(started))


def eta_pipeline(steps_done: int, steps_total: int, started_at) -> float | None:
    """流水线运行：步数比例线性估剩余（至少 2 步且已开始计时）"""
    if not started_at or not steps_total or steps_total < 2:
        return None
    started = _as_epoch(started_at) if isinstance(started_at, (datetime, str)) else float(started_at)
    return eta_from_progress(steps_done / steps_total * 100, max(time.time() - started, 0))


def _as_epoch(dt) -> float:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


async def predict_learning(db: AsyncSession, user_id: int, course_id: int) -> dict:
    """通识课学习进度线性预测：近 14 天完成节数外推「预计 X 天后学完」。"""
    from app.database.models import GeneralCourse, GeneralLesson, GeneralProgress

    course = (await db.execute(
        select(GeneralCourse).where(GeneralCourse.id == course_id))).scalar_one_or_none()
    if not course:
        return {"status": "not_found"}
    total_lessons = (await db.execute(
        select(GeneralLesson.id).where(GeneralLesson.course_id == course_id,
                                       GeneralLesson.status == "ready"))).scalars().all()
    total = len(total_lessons)
    rows = (await db.execute(
        select(GeneralProgress.percent, GeneralProgress.status, GeneralProgress.updated_at)
        .where(GeneralProgress.user_id == user_id, GeneralProgress.course_id == course_id)
    )).all()
    done = sum(1 for p, s, _ in rows if s == "done" or (p or 0) >= 100)
    started_lessons = len(rows)
    out = {"status": "ok", "total_lessons": total, "done_lessons": done,
           "started_lessons": started_lessons,
           "percent": round(done / total * 100, 1) if total else 0.0}
    if total == 0 or done == 0:
        out["status"] = "not_started" if done == 0 else "insufficient"
        out["estimated_days_left"] = None
        return out
    # 近 14 天每日完成量（updated_at 落在哪一天）
    since = datetime.now(timezone.utc) - timedelta(days=14)
    per_day = [0] * 14
    for _p, _s, upd in rows:
        if not upd:
            continue
        u = _as_epoch_dt(upd)
        if u < since:
            continue
        idx = min(13, (u - since).days)
        per_day[idx] += 1
    series = [float(x) for x in per_day]
    active_days = sum(1 for x in series if x > 0)
    if active_days < 3:
        # 学习频次太稀疏不硬造预测，用总量均值兜底
        rate = done / 14.0
        out["basis"] = "average"
    else:
        fc = linear_forecast(series)
        rate = max(fc["predicted"], 0.05) if fc["status"] == "ok" else done / 14.0
        out["basis"] = "forecast"
        out["confidence"] = fc.get("confidence")
    remaining = total - done
    out["daily_rate"] = round(rate, 3)
    out["estimated_days_left"] = int(remaining / rate) + 1 if rate > 0 else None
    return out


def _as_epoch_dt(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
