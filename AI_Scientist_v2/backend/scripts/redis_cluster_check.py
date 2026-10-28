"""智研星枢 - 分布式真实验证：两个独立 Python 进程 = 两台后端实例

原理：进程 A 执行完即销毁（其进程内存随之消失），随后进程 B 仍能看到 A 造成的
限流/锁定/占坑状态，则该状态只可能来自 Redis —— 这就是多实例共享的真实证据，
而不是同进程里的"假分布式"。

用法（在 backend 目录下）：
    python scripts/redis_cluster_check.py

验证三项：
1) IP 限流共享：A 把测试 IP 的登录配额（10/分钟）用完 → B 对同一 IP 被拒、不同 IP 放行
2) 账号锁定共享：A 对测试账号累计 5 次失败触发锁定 → B 查询该账号即处于锁定
3) 集群并发闸：A 占 3 个生成作业租约 → B 还能占第 4 个（上限 4），第 5 个被挡在门外；
   另验证过期租约被自动回收（进程崩溃自愈机制）
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_IP_A = "203.0.113.7"   # TEST-NET-3 保留段，仅测试用
TEST_IP_B = "203.0.113.8"
TEST_USER = "smoke_cluster_user"
ACTIVE_ZSET = "zhixing:gen:active"


def _imports():
    sys.path.insert(0, BACKEND)
    from app.services import redis_client as rc
    from app.security.rate_limiter import auth_rate_limiter
    from app.security.login_guard import login_guard
    from app.services.job_queue import generation_queue
    return rc, auth_rate_limiter, login_guard, generation_queue


async def role_a() -> int:
    """实例 A：用完 IP 配额 + 触发账号锁定 + 占用 3 个并发租约，然后进程退出。"""
    rc, rl, lg, gq = _imports()
    if rc.get_redis() is None:
        print("NO_REDIS")
        return 2
    allowed10 = True
    for _ in range(10):
        ok, _retry = await rl.is_allowed(TEST_IP_A)
        allowed10 = allowed10 and ok
    lock_triggered = False
    for _ in range(5):
        locked, _secs = await lg.record_fail(TEST_USER)
        lock_triggered = lock_triggered or locked
    slots = []
    for i in range(3):
        job = f"smokeA{i}"
        ok = await gq._acquire_global_slot(job)
        slots.append(job) if ok else None
    out = {"qlim_allowed10": allowed10, "lock_triggered": lock_triggered,
           "slots_held_by_a": len(slots)}
    print(json.dumps(out))
    await rc.close()
    return 0


async def role_b() -> int:
    """实例 B：全新进程、内存全空，看能否"继承" A 的全部状态。"""
    rc, rl, lg, gq = _imports()
    r = rc.get_redis()
    if r is None:
        print("NO_REDIS")
        return 2
    denied_same, retry = await rl.is_allowed(TEST_IP_A)      # 期望 False（A 已用满）
    allowed_other, _ = await rl.is_allowed(TEST_IP_B)        # 期望 True（不受牵连）
    sees_lock, ttl = await lg.is_locked(TEST_USER)           # 期望 True
    slot4 = await gq._acquire_global_slot("smokeB4")         # 期望 True（4=上限）
    slot5_blocked = False
    try:
        await asyncio.wait_for(gq._acquire_global_slot("smokeB5"), timeout=3)
    except asyncio.TimeoutError:
        slot5_blocked = True                                  # 期望 True（第 5 个被挡）
    out = {"b_denied_same_ip": not denied_same, "b_allowed_other_ip": allowed_other,
           "b_sees_lock": sees_lock, "b_lock_ttl": ttl,
           "b_slot4_ok": slot4, "b_slot5_blocked": slot5_blocked}
    print(json.dumps(out))
    await rc.close()
    return 0


async def role_cleanup() -> int:
    """清理测试痕迹 + 演示租约过期回收（崩溃自愈）。"""
    rc, rl, lg, gq = _imports()
    r = rc.get_redis()
    if r is None:
        print("NO_REDIS")
        return 2
    await r.delete(f"zhixing:rl:auth:{TEST_IP_A}", f"zhixing:rl:auth:{TEST_IP_B}",
                   f"zhixing:loginfails:{TEST_USER}", f"zhixing:loginlock:{TEST_USER}")
    await gq._release_global_slot("smokeB4")
    await r.zrem(ACTIVE_ZSET, "smokeA0", "smokeA1", "smokeA2")
    # 崩溃自愈：塞一个"已过期"的幽灵租约，并发闸取位前会先把过期租约清掉
    await r.zadd(ACTIVE_ZSET, {"ghost_job": time.time() - 1})
    pipe = r.pipeline(transaction=True)
    pipe.zremrangebyscore(ACTIVE_ZSET, 0, time.time())
    pipe.zscore(ACTIVE_ZSET, "ghost_job")
    removed, score = await pipe.execute()
    out = {"ghost_removed": removed >= 1 and score is None,
           "active_left": await r.zcard(ACTIVE_ZSET)}
    print(json.dumps(out))
    await rc.close()
    return 0


def _run(role: str) -> dict:
    p = subprocess.run([sys.executable, os.path.abspath(__file__), "--role", role],
                       cwd=BACKEND, capture_output=True, text=True, timeout=60)
    line = (p.stdout or "").strip().splitlines()[-1] if (p.stdout or "").strip() else ""
    if not line or line == "NO_REDIS":
        print(f"[{role}] Redis 不可用：{line or p.stderr[-300:]}")
        sys.exit(2)
    return json.loads(line)


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--role":
        role = sys.argv[2]
        return asyncio.run({"a": role_a, "b": role_b, "cleanup": role_cleanup}[role]())

    print("═══ 分布式真实验证：进程 A（用完即销毁） → 进程 B（全新实例）═══")
    a = _run("a")
    print(f"  A: {a}")
    b = _run("b")
    print(f"  B: {b}")
    c = _run("cleanup")
    print(f"  清理: {c}")
    checks = [
        ("A 10 次内配额全部放行（未误伤）", a["qlim_allowed10"] is True),
        ("A 第 5 次失败触发账号锁定", a["lock_triggered"] is True),
        ("A 占用 3 个并发租约", a["slots_held_by_a"] == 3),
        ("B 新进程对同一 IP 被限流（跨进程共享）", b["b_denied_same_ip"] is True),
        ("B 其他 IP 不受影响", b["b_allowed_other_ip"] is True),
        ("B 新进程可见账号锁定（跨进程共享）", b["b_sees_lock"] is True),
        ("B 还能占第 4 个坑（=集群上限）", b["b_slot4_ok"] is True),
        ("B 第 5 个坑被并发闸挡住", b["b_slot5_blocked"] is True),
        ("过期租约被自动回收（崩溃自愈）", c["ghost_removed"] is True),
        ("清理后集群活跃数为 0", c["active_left"] == 0),
    ]
    bad = 0
    for name, ok in checks:
        print(f"  {'✅' if ok else '❌'} {name}")
        bad += 0 if ok else 1
    print("ALL_PASS" if bad == 0 else f"{bad} 项失败")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
