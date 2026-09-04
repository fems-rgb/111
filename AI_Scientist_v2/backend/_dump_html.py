# -*- coding: utf-8 -*-
"""dump 生成的 HTML，看图表 img 标签 + 占位"""
import asyncio
from app.database.session import AsyncSessionLocal
from app.api.v1.export import _build_p1_to_p20, TeamConfig, auto_export_pdf
from app.database.models import Project, AgentTask, Hypothesis, IterationRecord
import app.api.v1.export as exp
import markdown as md_lib

async def main():
    async with AsyncSessionLocal() as db:
        pid = 1
        proj = (await db.execute(exp.select(Project).where(Project.id == pid))).scalar_one()
        tasks = (await db.execute(exp.select(AgentTask).where(AgentTask.project_id == pid))).scalars().all()
        hypos = (await db.execute(exp.select(Hypothesis).where(Hypothesis.project_id == pid))).scalars().all()
        iters = (await db.execute(exp.select(IterationRecord).where(IterationRecord.project_id == pid))).scalars().all()
        team = TeamConfig()
        md = _build_p1_to_p20(proj, tasks, hypos, iters, team)
        print(f"[Markdown] {len(md)//1024} KB, 图表字段出现: {md.count('图表')} 次")

        html_body = md_lib.markdown(md, extensions=['tables', 'fenced_code'])
        print(f"[HTML] <img> 标签数: {html_body.count('<img')}")
        out = r"D:\111-1\AI_Scientist_v2\backend\_debug.html"
        open(out, "w", encoding="utf-8").write(html_body)
        print(f"[dump] {out}")

        # 直接跑完整导出，抓日志
        print("\n=== 完整导出（看 stage 日志）===")
        res = await auto_export_pdf(pid, db)
        print(f"[结果] {res}")

asyncio.run(main())
