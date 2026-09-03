"""补丁1: 直接生成模式两个 document_path 赋值点改为 PDF 优先"""
from pathlib import Path

FILE = Path(__file__).parent / "app" / "api" / "v1" / "questions.py"
content = FILE.read_text(encoding="utf-8")
lines = content.splitlines(keepends=True)

applied = 0

# ========== 锚点A: task.document_path = report_path ==========
for i, line in enumerate(lines):
    if "task.document_path = report_path" in line and "report.md" in "".join(lines[max(0,i-3):i]):
        indent = line[:len(line) - len(line.lstrip())]
        block = [
            indent + "# ★ PDF为主交付物\n",
            indent + "from app.api.v1.export import md_to_pdf\n",
            indent + '_pdf_rp = report_path.replace("report.md", "report.pdf")\n',
            indent + "_md_a = open(report_path, 'r', encoding='utf-8').read()\n",
            indent + "if md_to_pdf(_md_a, _pdf_rp):\n",
            indent + "    task.document_path = _pdf_rp\n",
            indent + '    logger.info("✅ PDF已生成(主交付物): %s" % _pdf_rp)\n',
            indent + "else:\n",
            indent + "    task.document_path = report_path\n",
            indent + '    logger.warning("⚠️ PDF失败，回退Markdown")\n',
        ]
        lines[i:i+1] = block
        applied += 1
        print("✅ 锚点A已应用 @ 原行%d" % (i+1))
        break

# ========== 锚点B: task.document_path = doc_path ==========
for i, line in enumerate(lines):
    if "task.document_path = doc_path" in line and "final_output" in "".join(lines[max(0,i-5):i]):
        indent = line[:len(line) - len(line.lstrip())]
        block = [
            indent + "# ★ PDF为主交付物\n",
            indent + "from app.api.v1.export import md_to_pdf\n",
            indent + '_pdf_dp = doc_path.replace("report.md", "report.pdf")\n',
            indent + "if md_to_pdf(project.final_output, _pdf_dp):\n",
            indent + "    task.document_path = _pdf_dp\n",
            indent + '    logger.info("✅ PDF已生成(主交付物): %s" % _pdf_dp)\n',
            indent + "else:\n",
            indent + "    task.document_path = doc_path\n",
            indent + '    logger.warning("⚠️ PDF失败，回退Markdown")\n',
        ]
        lines[i:i+1] = block
        applied += 1
        print("✅ 锚点B已应用 @ 原行%d" % (i+1))
        break

if applied > 0:
    FILE.write_text("".join(lines), encoding="utf-8")
    print("\n🎉 补丁1完成，共应用%d个锚点。请重启后端。" % applied)
else:
    print("\n❌ 未命中任何锚点")