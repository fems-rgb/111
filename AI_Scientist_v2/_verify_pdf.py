import pdfplumber, glob, os

# 自动找最新生成的 PDF
cands = glob.glob(r"D:\111-1\AI_Scientist_v2\**\*.pdf", recursive=True)
cands = [c for c in cands if os.path.basename(c).lower().endswith(".pdf")]
cands.sort(key=os.path.getmtime, reverse=True)
path = cands[0] if cands else None
print("验证文件:", path)

with pdfplumber.open(path) as pdf:
    A4 = 595.3
    print(f"共 {len(pdf.pages)} 页\n")
    bad = []
    for pi, page in enumerate(pdf.pages):
        mx = max((w["x1"] for w in page.extract_words()), default=0)
        if mx > A4 + 5:
            bad.append((pi + 1, round(mx, 1)))
    if bad:
        print("⚠️ 仍溢出页面:")
        for p, x in bad:
            print(f"  P{p}: max_x={x} (超 {round(x-A4,1)}pt)")
    else:
        print("✅ 所有页面无横向溢出 (max_x ≤ 600)")
