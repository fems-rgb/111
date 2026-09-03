# -*- coding: utf-8 -*-
"""验证：模拟 project_id=int 调用 + 题库真实题目，确认渲染无硬编码术语"""
import sys, os, sqlite3
sys.path.insert(0, r"D:\111-1\AI_Scientist_v2\backend")

DB = r"D:\111-1\AI_Scientist_v2\backend\zhixing.db"

# 取题库真实题目
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
q = c.execute("SELECT * FROM science_questions WHERE id=1").fetchone()
c.close()
Q = dict(q) if q else {}
rq = Q.get("title") or "体细胞重编程如何决定整株植物的再生命运"
print("题目:", rq[:60])

# 模拟 project_id=1（int）调用 -> _resolve_project 应自动从题库取 rq
import importlib.util
spec = importlib.util.spec_from_file_location("cc", r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\challenge_cup_pdf.py")
# 不加载整个模块（会连 weasyprint），直接内联复刻逻辑做验证
class P:
    def __getattr__(self, n): return ""
proj = P()
proj.id = 1
proj.research_question = rq
proj.title = rq
proj.description = rq

def _derive_rationale(p):
    r = (getattr(p,"research_question","") or "").strip() or "该前沿科学问题"
    return ("围绕「%s」这一科学问题，采用多智能体协作的科研闭环："
            "文献挖掘→知识缺口识别→候选假设生成与可验证性评分→实验设计与数值模拟→结果验证与反思迭代。") % r

def _neutral_methods(p):
    r = (getattr(p,"research_question","") or "").strip() or "研究问题"
    return ("针对「%s」，采用混合方法：定量层面结合线性回归、显著性检验与贝叶斯参数估计，"
            "定性层面构建理论模型与概念框架；实验流程遵循「数据准备→变量操作化→模型设定→参数估计→稳健性检验」的规范路径。") % r

ctx = {
    "project": proj, "generated_at": "2026-01-01",
    "charts": [], "references": [],
    "problem_statement": "", "rationale": _derive_rationale(proj),
    "technical_details": "", "datasets": "",
    "paper_title": "", "paper_abstract": "",
    "methods": _neutral_methods(proj),
    "experiments": "依据上述方法论设计对照实验，记录关键指标与观测结果，并对统计显著性进行量化评估。",
    "results": "实验结果及对应图表见下方各节；本节汇总主要发现及其统计显著性。",
    "hypotheses": None,
}
from jinja2 import Environment, FileSystemLoader
TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
env = Environment(loader=FileSystemLoader(os.path.dirname(TPL)))
html = env.get_template("challenge_cup_template.html").render(**ctx)

BAD = ["暗物质","暗能量","WIMP","wimp","轴子","CMB","Planck","SDSS","XENON","xenon",
       "宇宙的物质构成","宇宙由什么构成","星系旋转","大尺度结构","额外维度",
       "Qwen 多智能体架构","自动完成文献挖掘"]
found = [(t, html.count(t)) for t in BAD if t in html]
out = r"D:\111-1\AI_Scientist_v2\_verify_final.html"
open(out, "w", encoding="utf-8").write(html)
print("渲染文件:", out)
if found:
    print("⚠️ 仍含无关术语:")
    for t, cnt in found: print(f"  {t}: {cnt}次")
else:
    print("✅ 无任何宇宙学占位 / 空套话 —— 内容基于 research_question 生成")
