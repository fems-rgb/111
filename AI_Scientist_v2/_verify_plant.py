# -*- coding: utf-8 -*-
"""升级验证：用非宇宙题目 + 扫描模板自身全部硬编码领域词"""
import sys, os, re

TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
src = open(TPL, encoding="utf-8").read()

TERMS = ["暗物质","暗能量","WIMP","wimp","CMB","Planck","SDSS","XENON","xenon",
         "星系旋转","大尺度结构","额外维度","轴子","宇宙的物质构成","宇宙由什么构成"]

# 1) 扫描模板正文（去 style / Jinja）
print("="*70)
print("[1] 模板正文残留的领域词（去 style/Jinja 后）")
print("="*70)
body = re.sub(r"<style>.*?</style>", "", src, flags=re.S)
body = re.sub(r"\{%.*?%\}", "", body, flags=re.S)
body = re.sub(r"\{\{.*?\}\}", "VAR", body, flags=re.S)
body_text = re.sub(r"<[^>]+>", "", body)
hits = [(t, body_text.count(t)) for t in TERMS if t in body_text]
if hits:
    print("⚠️ 模板正文仍含:")
    for t, c in hits: print(f"  {t}: {c}次")
    # 列上下文
    for t, c in hits:
        for m in re.finditer(r".{0,50}"+t+r".{0,50}", body_text):
            print(f"    ...{m.group()[:110]}...")
else:
    print("✅ 模板正文无任何硬编码领域词")

# 2) 用植物题目渲染
print()
print("="*70)
print("[2] 用植物题目渲染验证")
print("="*70)
class P:
    def __getattr__(self, n): return ""
proj = P()
proj.id = 1
proj.research_question = "体细胞重编程如何决定整株植物的再生命运"
proj.title = "从体细胞到整株：细胞命运重编程的调控机制"
proj.description = "探究植物体细胞如何通过重编程获得再生全能性"

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
env = Environment(loader=FileSystemLoader(os.path.dirname(TPL)))
html = env.get_template("challenge_cup_template.html").render(**ctx)
html_text = re.sub(r"<style>.*?</style>", "", html, flags=re.S)
html_text = re.sub(r"<[^>]+>", "", html_text)

found = [(t, html_text.count(t)) for t in TERMS if t in html_text]
out = r"D:\111-1\AI_Scientist_v2\_verify_plant.html"
open(out, "w", encoding="utf-8").write(html)
print("渲染文件:", out)
print("题目: 体细胞重编程如何决定整株植物的再生命运")
if found:
    print("⚠️ 渲染结果仍含无关术语:")
    for t, c in found: print(f"  {t}: {c}次")
else:
    print("✅ 渲染结果无任何宇宙学占位 / 空套话 —— 对植物题目完全干净")
