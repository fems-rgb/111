# -*- coding: utf-8 -*-
"""
对标赛题 XH-202619 的 PDF 生成器
- 用已有的 challenge_cup_template.html (Jinja2) 渲染
- WeasyPrint 转 PDF
- 自动扫描实验图表 base64 嵌入
- References 从 project.literature_refs 读取（真实检索结果）
- 唯一文件名（防 Permission denied）
"""
import base64, glob, json, os, re, time, uuid
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

TPL_DIR = Path(__file__).resolve().parent / "templates"
_CDIR = Path(__file__).resolve().parent.parent.parent.parent / "output" / "pdf_reports"
_CDIR.mkdir(parents=True, exist_ok=True)

_env = Environment(loader=FileSystemLoader(str(TPL_DIR)), autoescape=select_autoescape(["html"]))

_LATEX_MAP = {r"\alpha":"α",r"\beta":"β",r"\gamma":"γ",r"\delta":"δ",r"\theta":"θ",
              r"\lambda":"λ",r"\mu":"μ",r"\pi":"π",r"\sigma":"σ",r"\omega":"ω",r"\Omega":"Ω",
              r"\Lambda":"Λ",r"\Delta":"Δ",r"\infty":"∞",r"\sum":"∑",r"\int":"∫",
              r"\times":"×",r"\pm":"±",r"\leq":"≤",r"\geq":"≥"}

def _latex(text):
    for k,v in _LATEX_MAP.items(): text=text.replace(k,v)
    return re.sub(r"\$(.+?)\$", r"\1", text)

def _charts(project_id):
    base = Path(__file__).resolve().parent.parent.parent.parent / "output" / "experiments"
    charts = []
    for d in [base / f"project_{project_id}", base / f"{project_id}"]:
        if d.exists():
            for ext in ("*.png","*.jpg","*.jpeg"):
                for p in glob.glob(str(d/ext)):
                    try:
                        with open(p,"rb") as f:
                            charts.append({"name":Path(p).stem,"b64":base64.b64encode(f.read()).decode()})
                    except: pass
    return charts

def _refs(project):
    raw = getattr(project, "literature_refs", None) or "[]"
    try: return json.loads(raw) if isinstance(raw,str) else raw
    except: return []

def generate_challenge_cup_pdf(project) -> str:
    """主入口：传入 Project ORM 对象，返回生成的 PDF 路径"""
    pid = getattr(project,"id",0)
    title = _latex(getattr(project,"title","") or f"Project {pid}")
    desc = _latex(getattr(project,"description","") or "（待补充）")

    # 把图表注入到模板上下文（模板里用 {% for c in charts %}）
    charts = _charts(pid)
    refs = _refs(project)

    ctx = {
        "project": project,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "charts": charts,
        "references": refs,
        "problem_statement": _latex(getattr(project,"problem_statement",desc) or desc),
        "rationale": _latex(getattr(project,"rationale","") or "基于 Qwen 多智能体架构，自动完成文献挖掘→知识缺口识别→假设生成→实验模拟→结果验证的闭环。"),
        "technical_details": getattr(project,"technical_details","") or "",
        "datasets": getattr(project,"datasets","") or "",
        "paper_title": getattr(project,"paper_title","") or title,
        "paper_abstract": _latex(getattr(project,"paper_abstract","") or desc),
        "methods": _latex(getattr(project,"methods","") or "（待补充）"),
        "experiments": _latex(getattr(project,"experiments","") or "（待补充）"),
        "results": _latex(getattr(project,"results","") or "实验结果见下方图表。"),
        "hypotheses": getattr(project,"hypotheses",None),
    }

    tpl = _env.get_template("challenge_cup_template.html")
    html = tpl.render(**ctx)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    suf = uuid.uuid4().hex[:6]
    out = _CDIR / f"challenge_cup_project_{pid}_{stamp}_{suf}.pdf"
    HTML(string=html).write_pdf(str(out))
    return str(out)
