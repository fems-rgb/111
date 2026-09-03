# -*- coding: utf-8 -*-
"""
修复 export.py 硬编码（宇宙学占位符）→ 基于真实 research_question 动态生成
基于 _readexport.py 的真实行内容（L703-796）精准锚定，幂等可重跑
"""
p = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"
src = open(p, encoding="utf-8").read()

# ── 1) L703-706: _rq 默认值 '宇宙由什么构成' → 通用 ──
old = """        _rq=str(proj.research_question or '宇宙由什么构成')
        _rq=_re.sub(r'科学问题[:：][^\\n]*','',_rq)
        _rq=_re.sub(r'问题描述[:：][^\\n]*','',_rq)
        _rq=_rq.replace('\\n',' ').strip() or '宇宙由什么构成'"""
new = """        _rq=str(proj.research_question or proj.description or '').strip()
        _rq=_re.sub(r'科学问题[:：][^\\n]*','',_rq)
        _rq=_re.sub(r'问题描述[:：][^\\n]*','',_rq)
        _rq=_rq.replace('\\n',' ').strip() or '该前沿科学问题'"""
if old in src:
    src = src.replace(old, new, 1); print("[修改1] _rq 默认值 -> 用 research_question/description")
else:
    print("[跳过1] 锚点未匹配")

# ── 2) L708-712: 背景段硬编码宇宙举例 → 通用动态描述 ──
old = ("""        if not _re.search(r'(局限|不足|挑战|困难|难以|瓶颈|低效)',ps):
            ps=('在传统人工科研模式下，围绕“'+_rq+'”这一科学问题的探索，'
                '高度依赖研究者个人经验与文献积累；面对暗物质候选粒子（WIMP/轴子）、暗能量状态方程、'
                '额外维度等多方向并存，且涉及 XENON 直接探测、Planck CMB 功率谱、SDSS 巡天等'
                '多模态实测数据的复杂局面时，人工梳理效率低下、易陷入思维定式，'
                '难以在假设生成之初即保证其可验证性与自洽性，亦难以系统覆盖全部候选方向并给出可操作检验路径。\\n\\n'+ps)""")
new = ("""        if not _re.search(r'(局限|不足|挑战|困难|难以|瓶颈|低效)',ps):
            ps=('在传统人工科研模式下，围绕“'+_rq+'”这一科学问题的探索，'
                '高度依赖研究者个人经验与文献积累；面对研究对象的多层次机制与相互关联的关键变量，'
                '且需整合多源异构实测数据与跨学科理论时，'
                '人工梳理效率低下、易陷入思维定式，'
                '难以在假设生成之初即保证其可验证性与自洽性，亦难以系统覆盖全部候选方向并给出可操作检验路径。\\n\\n'+ps)""")
if old in src:
    src = src.replace(old, new, 1); print("[修改2] 背景段领域举例 -> 通用动态")
else:
    print("[跳过2] 锚点未匹配（按 _readexport 输出微调）")

# ── 3) L733: rationale 研究对象默认值 '宇宙的物质构成' ──
old = """        rationale=('推导链条：①知识缺口识别（研究对象：'+(_ro or '宇宙的物质构成')+'，锁定关键变量）→ '"""
new = """        rationale=('推导链条：①知识缺口识别（研究对象：'+(_ro or _rq or '研究问题本身')+'，锁定关键变量）→ '"""
if old in src:
    src = src.replace(old, new, 1); print("[修改3] rationale 研究对象 -> _rq 动态")
else:
    print("[跳过3] 锚点未匹配")

# ── 4) L774: methods 短时的 fallback 含 Planck/SDSS/XENON ──
old = ("""                methods=('研究设计类型：混合方法，定量（Planck CMB功率谱/SDSS大尺度结构/XENON直接探测、线性回归、显著性检验、贝叶斯参数估计）与定性（理论模型与概念框架）结合。实验流程：①数据准备→②变量操作化→③计量模型设定→④参数估计→⑤稳健性检验→""")
new = ("""                methods=('研究设计类型：混合方法，针对研究对象的关键变量采用线性回归、显著性检验、贝叶斯参数估计等定量方法，并结合理论模型与概念框架的定性分析。实验流程：①数据准备→②变量操作化→③计量模型设定→④参数估计→⑤稳健性检验→""")
if old in src:
    src = src.replace(old, new, 1); print("[修改4] methods fallback -> 通用方法")
else:
    print("[跳过4] 锚点未匹配")

open(p, "w", encoding="utf-8").write(src)
print("\n[完成] export.py 硬编码已参数化")
import py_compile
try:
    py_compile.compile(p, doraise=True); print("[syntax] OK")
except py_compile.PyCompileError as e:
    print(f"[syntax] L{e.lineno}: {e.msg}")
