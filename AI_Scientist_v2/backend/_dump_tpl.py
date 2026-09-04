# -*- coding: utf-8 -*-
"""把 export.py 的 TEMPLATE 模板完整 dump 出来，看图表怎么渲染"""
import re
P = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"
t = open(P, encoding="utf-8", errors="ignore").read()

# 找模板：通常是 TEMPLATE = """..."""
m = re.search(r'TEMPLATE\s*=\s*["\u201c\u201d](.*?)["\u201c\u201d]', t, re.S)
if not m:
    # 也可能是 f-string / 直接拼接
    print("未找到 TEMPLATE = \"\"\" 形式，改用行号定位")
else:
    tmpl = m.group(1)
    out = r"D:\111-1\AI_Scientist_v2\backend\_template.txt"
    open(out, "w", encoding="utf-8").write(tmpl)
    print(f"[dump] 模板 ({len(tmpl)//1024} KB) -> {out}")
    print(f"\n=== 模板里 <img 出现: {tmpl.count('<img')} 次 ===")
    print(f"=== 模板里 charts 出现: {tmpl.count('charts')} 次 ===")
    print(f"=== 模板里 {{% for 出现: {tmpl.count('{% for')} 次 ===")

# 无论如何，搜索模板里所有 img / charts / for 循环
print("\n=== 整个 export.py 里 <img 出现位置 ===")
for i, l in enumerate(t.split("\n")):
    if "<img" in l:
        print(f"L{i+1:>3}| {l.strip()[:240]}")
