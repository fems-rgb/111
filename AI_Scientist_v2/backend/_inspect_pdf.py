# -*- coding: utf-8 -*-
"""检查最新生成的 PDF：有没有嵌入图片 + 文本内容抽样"""
import glob, os
files = sorted(glob.glob(r"D:\111-1\AI_Scientist_v2\backend\output\pdf_reports\*.pdf"))
if not files:
    print("(无 PDF，先跑 _v2_pdf_detail.py)"); raise SystemExit
fp = files[-1]
print(f"检查: {os.path.basename(fp)} ({os.path.getsize(fp)//1024} KB)")

# 用 pdf 库看图片数 + 文本
try:
    from pypdf import PdfReader
    r = PdfReader(fp)
    print(f"页数: {len(r.pages)}")
    txt = r.pages[0].extract_text() or ""
    print(f"首页文本前 500 字:\n{txt[:500]}")
    # 图片
    img_count = sum(1 for p in r.pages for _ in (p.images or []))
    print(f"嵌入图片总数: {img_count}")
except Exception as e:
    print(f"pypdf 不可用: {e}")

# 也看看原始 HTML 里图表标签
print("\n=== 提示：需看 export.py 生成的 html_body ===")
