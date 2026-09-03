# -*- coding: utf-8 -*-
"""
修复 challenge_cup_template.html 表格横向溢出 + 排版美化
针对已发现的 3 个问题精准修改（幂等，可重复运行）：
  L12 table: 加 table-layout:fixed + max-width
  L14 th nowrap: 改为允许折行（短表头仍可单行，宽表头折行）
  L15 td:first-child nowrap: 改为 normal（允许第一列折行）
  + 新增防溢出/跨页规则 + 三个宽表的 colgroup 显式列宽
"""
import re

TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
src = open(TPL, encoding="utf-8").read()

# ── 1) 修改 L12-15 的 table/th/td 规则 ──
fixes = [
    # table 加 fixed 布局 + 强制宽度
    (
        '  table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 9.5pt; }',
        '  table { border-collapse: collapse; table-layout: fixed; width: 100%; max-width: 100%; margin: 8px 0; font-size: 9.5pt; overflow-wrap: anywhere; }'
    ),
    # th 允许折行（白名单：不再强制 nowrap）
    (
        '  th { background: #e8eaf6; white-space: nowrap; }',
        '  th { background: #e8eaf6; white-space: normal; overflow-wrap: anywhere; }'
    ),
    # 第一列允许折行（关键：原来是 nowrap 撑破宽度）
    (
        '  table td:first-child { white-space: nowrap; }',
        '  table td:first-child { white-space: normal; overflow-wrap: anywhere; }'
    ),
]
for old, new in fixes:
    if old in src:
        src = src.replace(old, new, 1)
        print("[修改]", old.strip()[:50], "... ->", new.strip()[:50])
    else:
        print("[跳过/未匹配]", old.strip()[:60])

# ── 2) 在 </style>(L20 主样式) 前追加防溢出 + 美化规则 ──
ADDITIONAL = """
  /* === 修复宽表格横向溢出 (challenge_cup) === */
  table { word-break: break-word; }
  th, td { white-space: normal !important; overflow-wrap: anywhere !important; word-break: break-word; }
  /* 长文本单元格：紧凑行高，避免巨大空白 */
  td { line-height: 1.4; }
  /* 跨页：表头重复，行不拦腰断 */
  thead { display: table-header-group; }
  tr { break-inside: avoid; page-break-inside: avoid; }
  /* 代码/路径/URL 强制换行 */
  code, pre, .mono { word-break: break-all; overflow-wrap: anywhere; }
  /* 宽表（5列以上）整体缩小字号，挤下长段落 */
  table.wide-table, table.evidence-table, table.eval-table { font-size: 8.6pt; }
  table.wide-table th, table.wide-table td,
  table.evidence-table th, table.evidence-table td,
  table.eval-table th, table.eval-table td { padding: 3px 5px; line-height: 1.32; }
"""
if "<!-- === 修复宽表格" in src or "修复宽表格横向溢出" in src:
    print("[跳过] 附加规则已注入")
else:
    src = src.replace("</style>", ADDITIONAL + "  </style>", 1)

# ── 3) 给宽表加 colgroup 显式列宽（合计100%）──
# 先给三个已知宽表加 class（如果它们还没 class），再插入 colgroup
# 定位各 <table> 及其表头列数
def add_colgroup(table_html):
    if "<colgroup>" in table_html:
        return table_html
    ths = re.findall(r"<th[^>]*>.*?</th>", table_html, re.S)
    n = len(ths)
    if n < 2:
        return table_html
    # 列宽方案（按文档分析的列，合计100）
    if n == 5:
        # 证据来源表 / 方案表：给长文本列(核心发现/数据方案/反向证据)更多宽度
        widths = [14, 20, 22, 22, 22]
    elif n == 8:
        # 假设评估表：等宽
        widths = [12.5]*8
    else:
        w = round(100/n, 1)
        widths = [w]*n
    total = sum(widths)
    widths = [round(x*100/total, 1) for x in widths]
    cg = "<colgroup>" + "".join(f'<col style="width:{w}%"/>' for w in widths) + "</colgroup>"
    # 在 <table ...> 后、<thead>/<tr> 前插入
    return re.sub(r"(<table[^>]*>)", r"\1" + cg, table_html, count=1)

src2 = re.sub(r"<table[^>]*>.*?</table>", lambda m: add_colgroup(m.group(0)), src, flags=re.S)

open(TPL, "w", encoding="utf-8").write(src2)

# ── 统计 ──
print()
print("="*64)
print("修复完成统计")
print("="*64)
final = open(TPL, encoding="utf-8").read()
print("  colgroup 数量:", final.count("<colgroup>"))
print("  table-layout:fixed:", "table-layout: fixed" in final)
print("  overflow-wrap anywhere:", final.count("overflow-wrap: anywhere"))
print("  L14 nowrap 残留:", "th { background: #e8eaf6; white-space: nowrap; }" in final)
print("  L15 nowrap 残留:", "table td:first-child { white-space: nowrap; }" in final)
