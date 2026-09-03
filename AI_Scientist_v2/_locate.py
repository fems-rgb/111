import os, glob

ROOT = r"D:\111-1\AI_Scientist_v2"

print("="*64)
print("A. HTML/Jinja2 报告模板")
print("="*64)
for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True) + \
         glob.glob(os.path.join(ROOT, "**", "*.jinja*"), recursive=True):
    if "node_modules" not in p:
        print("  " + p)

print()
print("="*64)
print("C. CSS 文件")
print("="*64)
for p in glob.glob(os.path.join(ROOT, "**", "*.css"), recursive=True):
    if "node_modules" not in p:
        print("  " + p)

print()
print("="*64)
print("D. Python 里引用 weasyprint/jinja 的位置")
print("="*64)
for p in glob.glob(os.path.join(ROOT, "backend", "**", "*.py"), recursive=True):
    try:
        with open(p, encoding="utf-8") as f:
            content = f.read()
        if any(k in content for k in ["weasyprint", "WeasyPrint", "from_string", "get_template", "render("]):
            print("  " + p)
    except Exception:
        continue
