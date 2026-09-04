# -*- coding: utf-8 -*-
"""pid=2 打印完整异常 + 检查 project 2 数据完整性"""
import traceback, logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s - %(message)s")

from app.api.v1.export import generate_challenge_cup_pdf

print("=== pid=2 完整异常 ===")
try:
    result = generate_challenge_cup_pdf(2)
    print(f"返回: {result}")
except Exception as e:
    print(f"❌ {type(e).__name__}: {e}")
    traceback.print_exc()

# 顺便检查 project 2 数据
print("\n=== 检查 project 2 数据完整性 ===")
import asyncio
from app.database.session import AsyncSessionLocal
from sqlalchemy import text
async def chk():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("""
            SELECT p.id, p.title, p.team_config, p.evidence_files,
                   (SELECT COUNT(*) FROM hypotheses h WHERE h.project_id=p.id) n_hyp,
                   (SELECT COUNT(*) FROM experiment_runs e WHERE e.project_id=p.id) n_exp
            FROM projects p WHERE p.id=2
        """))
        row = r.fetchone()
        print(f"  id={row[0]} title={row[1]!r}")
        print(f"  team_config={'有' if row[2] else '无/空'}")
        print(f"  evidence_files={'有' if row[3] else '无/空'}")
        print(f"  hypotheses={row[4]}  experiment_runs={row[5]}")
asyncio.run(chk())
