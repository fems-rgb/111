# -*- coding: utf-8 -*-
"""dump 生成的 HTML 到文件，直接看 <img> 标签和图表占位"""
import asyncio, os, re
from app.database.session import AsyncSessionLocal
from app.api.v1.export import auto_export_pdf, _build_p1_to_p20
from app.database.models import Project, AgentTask, Hypothesis, IterationRecord
import app.api.v1.export as exp

# 让 auto_export_pdf 跑完，然后我们重新构建 HTML（不写 PDF，只取 HTML）
async def main():
    async with AsyncSessionLocal() as db:
        pid = 1
        proj = (await db.execute(exp.select(Project).where(Project.id == pid))).scalar_one()
        tasks = (await db.execute(exp.select(AgentTask).where(AgentTask.project_id == pid))).scalars().all()
        hypos = (await db.execute(exp.select(Hypothesis).where(Hypothesis.project_id == pid))).scalars().all()
        iters = (await db.execute(exp.select(IterationRecord).where(IterationRecord.project_id == pid))).scalars().all()

        from app.api.v1.export import TeamConfig
        team = TeamConfig()
        if proj.competition_config:
            try:
                d = __import__("app.utils.safe_json", fromlist=["safe_json_parse"]).safe_json_parse(
                    proj.competition_config, fallback={}, label="dump")
                team = TeamConfig(**{k: v for k, v in d.items() if k in TeamConfig.model_fields})
            except Exception: pass

        md = _build_p1_to_p20(proj, tasks, hypos, iters, team)
        print(f"[Markdown] {len(md)//1024} KB")

        # 关键：找 export.py 里生成 html_body 的那行，把 html_body dump 出来
        # 直接调用内部函数 _render_html（如果存在），否则用正则抽 html_body 赋值
        # 退而求其次：直接看模板里 img 标签
        out = r"D:\111-1\AI_Scientist_v2\backend\_debug.html"
        # 读取 export.py 里的 TEMPLATE 字符串，渲染一个最小版
        import markdown as md_lib
        html_body = md_lib.markdown(md, extensions=['tables', 'fenced_code'])
        # 检查图表占位是否被替换
        has_img = "<img" in html_body
        print(f"[HTML] <img> 标签存在: {has_img}")
        print(f"[HTML] 'charts' 占位: {'{{charts}}' in html_body or '{charts}' in html_body}")
        open(out, "w", encoding="utf-8").write(html_body[:10000])
        print(f"\n[dump] 前 10KB HTML -> {out}")
        print("\n=== HTML 前 80 行（看图表占位/图片标签）===")
        print("\n".join(html_body.split("\n")[:80]))

asyncio.run(main())
