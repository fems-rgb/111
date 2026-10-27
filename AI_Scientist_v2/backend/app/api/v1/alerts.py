"""统一预警中心（Phase B）

GET /alerts 聚合四类数据驱动的预警（无人工规则配置，来源即事实）：
- cost_over_threshold    本月成本已超阈 / 线性预测将超阈（cost_daily + forecast）
- model_rate_limited     进程内被限流/屏蔽的模型（qwen_client.model_status）
- provider_key_missing   已注册但未配密钥的供应商（提示去 backend/.env 配置）
- job_failed             近 24h 失败的生成作业与流水线运行
返回始终为 {"ok": true, "alerts": [...]}，单类聚合失败只跳过不影响其余。
"""
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database.models import User, UserRole, GenerateJob, PipelineRun, Pipeline
from app.database.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["预警中心"])


def _alert(aid, atype, severity, title, message, action_label="", action_href=""):
    return {"id": aid, "type": atype, "severity": severity, "title": title,
            "message": message, "action_label": action_label, "action_href": action_href,
            "created_at": datetime.now(timezone.utc).isoformat()}


@router.get("")
async def list_alerts(user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    alerts: list[dict] = []
    alerts += await _cost_alerts(db)
    alerts += _model_alerts()
    alerts += _provider_alerts()
    alerts += await _job_alerts(db, user)
    order = {"error": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: (order.get(a["severity"], 9), a["created_at"]))
    return {"ok": True, "alerts": alerts}


# ════════════════ 成本 ════════════════

async def _cost_alerts(db: AsyncSession) -> list[dict]:
    out: list[dict] = []
    try:
        from app.services import prediction
        # 从子模块导入：包 __init__ 把 cost_tracker 名字遮蔽成了实例，这里正好要用的就是实例
        from app.observability.cost_tracker import cost_tracker
        threshold = settings.COST_ALERT_THRESHOLD_YUAN
        # 本进程累计成本已超阈（与既有日志预警同源，这里变成用户可见）
        if cost_tracker.total_cost >= threshold:
            out.append(_alert("cost-session-over", "cost_over_threshold", "error",
                              "API 成本已超预警线",
                              f"本服务运行以来累计 ¥{cost_tracker.total_cost:.2f}，"
                              f"超过预警阈值 ¥{threshold:.0f}。",
                              "查看成本明细", "/cost"))
        history = await prediction.cost_history(db, days=30)
        fc = prediction.predict_cost(history)
        if fc.get("status") == "ok":
            days = fc.get("exceed_threshold_in_days")
            if days == 0:
                pass  # 已由累计超阈覆盖，不重复报
            elif days is not None and days <= 14:
                out.append(_alert("cost-forecast-over", "cost_over_threshold", "warning",
                                  "成本预测：即将超预警线",
                                  f"按近 30 天趋势外推，本月预计花 ¥{fc['forecast_month_total_yuan']:.2f}，"
                                  f"约 {days} 天后超过阈值 ¥{threshold:.0f}（置信度 {fc.get('confidence')}）。",
                                  "查看成本明细", "/cost"))
    except Exception as e:
        logger.debug("[alerts] cost skip: %s", e)
    return out


# ════════════════ 模型限流 ════════════════

def _model_alerts() -> list[dict]:
    out: list[dict] = []
    try:
        from app.agents.qwen_client import model_status
        blocked = model_status()
        if blocked:
            names = "、".join(f"{m}（{(info.get('reason') or '暂不可用')[:30]}）"
                              for m, info in list(blocked.items())[:4])
            out.append(_alert("model-rate-limited", "model_rate_limited", "warning",
                              "部分模型临时受限",
                              f"近期被限流或屏蔽：{names}。生成时会自动换用其他可用模型，无需操作。",
                              "去课件工坊", "/courseware-studio"))
    except Exception as e:
        logger.debug("[alerts] model skip: %s", e)
    return out


# ════════════════ 供应商密钥 ════════════════

def _provider_alerts() -> list[dict]:
    out: list[dict] = []
    try:
        from app.agents import model_providers
        missing = [p for p in model_providers.providers() if not p.configured]
        if missing:
            names = "、".join(p.label for p in missing)
            envs = " / ".join(p.env_key for p in missing if p.env_key)
            out.append(_alert("provider-key-missing", "provider_key_missing", "info",
                              "有模型供应商尚未启用",
                              f"{names} 未配置 API Key（backend/.env 填 {envs} 即可启用并出现在模型下拉）。",
                              "", ""))
    except Exception as e:
        logger.debug("[alerts] provider skip: %s", e)
    return out


# ════════════════ 任务失败 ════════════════

async def _job_alerts(db: AsyncSession, user: User) -> list[dict]:
    out: list[dict] = []
    # SQLite 存的是无时区 UTC 串，比较基准也用 naive utcnow，避免 tz-aware 与库内值比对失真
    since = datetime.utcnow() - timedelta(hours=24)
    try:
        q = select(GenerateJob).where(GenerateJob.status == "failed",
                                      GenerateJob.updated_at >= since)
        if user.role != UserRole.ADMIN:
            q = q.where(GenerateJob.user_id == user.id)
        rows = (await db.execute(q.order_by(GenerateJob.updated_at.desc()).limit(5))).scalars().all()
        for j in rows:
            out.append(_alert(f"job-{j.job_id}", "job_failed", "error",
                              "课件生成失败",
                              f"《{(j.course_title or j.topic or '')[:40]}》生成失败：{(j.message or j.error or '')[:80]}",
                              "去课件工坊", "/courseware-studio"))
    except Exception as e:
        logger.debug("[alerts] jobs skip: %s", e)
    try:
        q = (select(PipelineRun, Pipeline.name)
             .join(Pipeline, Pipeline.id == PipelineRun.pipeline_id)
             .where(PipelineRun.status == "failed", PipelineRun.finished_at >= since))
        if user.role != UserRole.ADMIN:
            q = q.where(Pipeline.user_id == user.id)
        rows = (await db.execute(q.order_by(PipelineRun.finished_at.desc()).limit(5))).all()
        for run, pname in rows:
            out.append(_alert(f"run-{run.id}", "job_failed", "error",
                              "流水线运行失败",
                              f"「{pname}」最近一次运行失败（{len(run.steps_log or [])} 步已执行）。",
                              "查看自动化", "/automation"))
    except Exception as e:
        logger.debug("[alerts] runs skip: %s", e)
    return out
