"""自动将 questions.py 改为 PDF 优先输出"""
import re
from pathlib import Path

FILE = Path(__file__).parent / "app" / "api" / "v1" / "questions.py"

content = FILE.read_text(encoding="utf-8")
lines = content.splitlines(keepends=True)

# ========== 补丁1: 直接生成模式 ==========
# 锚点: task.document_path = _doc_path (且前面有 f.write(content))
patch1_applied = False
for i, line in enumerate(lines):
    if "task.document_path = _doc_path" in line and not patch1_applied:
        # 检查前3行是否有 f.write(content)，确保是直接生成模式
        context = "".join(lines[max(0,i-3):i])
        if "f.write(content)" in context or "write(content)" in context:
            indent = line[:len(line) - len(line.lstrip())]
            pdf_block = [
                f"{indent}# ★ Markdown仅作中间产物，PDF为主交付物\n",
                f"{indent}from app.api.v1.export import md_to_pdf\n",
                f'{indent}_pdf_path = _doc_path.replace("report.md", "report.pdf")\n',
                f"{indent}if md_to_pdf(content, _pdf_path):\n",
                f"{indent}    task.document_path = _pdf_path\n",
                f'{indent}    logger.info(f"✅ PDF已生成(主交付物): {{_pdf_path}}")\n',
                f"{indent}else:\n",
                f"{indent}    task.document_path = _doc_path\n",
                f'{indent}    logger.warning("⚠️ PDF生成失败，回退为Markdown")\n',
            ]
            # 替换当前行为整个pdf_block
            lines[i:i+1] = pdf_block
            patch1_applied = True
            print(f"✅ 补丁1(直接生成)已应用 @ 行{i+1}")
            break

if not patch1_applied:
    print("⚠️ 补丁1未找到锚点，可能已修改或代码结构不同")

# ========== 补丁2: 流水线模式 ==========
# 锚点: task.document_path = _report (且不在else分支里)
patch2_applied = False
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == "task.document_path = _report" and not patch2_applied:
        # 排除已经是补丁1的位置
        if "_pdf_path" in "".join(lines[max(0,i-5):i]):
            continue
        indent = line[:len(line) - len(line.lstrip())]
        pdf_block = [
            f"{indent}# ★ 流水线PDF为主交付物\n",
            f"{indent}from app.api.v1.export import md_to_pdf\n",
            f'{indent}_pdf_report = _report.replace("report.md", "report.pdf")\n',
            f'{indent}_md_content = open(_report, "r", encoding="utf-8").read()\n',
            f"{indent}if md_to_pdf(_md_content, _pdf_report):\n",
            f"{indent}    task.document_path = _pdf_report\n",
            f'{indent}    logger.info(f"✅ 流水线PDF已生成(主交付物): {{_pdf_report}}")\n',
            f"{indent}else:\n",
            f"{indent}    task.document_path = _report\n",
            f'{indent}    logger.warning("⚠️ 流水线PDF生成失败，回退为Markdown")\n',
        ]
        lines[i:i+1] = pdf_block
        patch2_applied = True
        print(f"✅ 补丁2(流水线)已应用 @ 行{i+1}")
        break

if not patch2_applied:
    print("⚠️ 补丁2未找到锚点，可能已修改或代码结构不同")

# 写回文件
if patch1_applied or patch2_applied:
    FILE.write_text("".join(lines), encoding="utf-8")
    print("\n🎉 修改完成！请重启后端服务。")
else:
    print("\n❌ 未应用任何补丁，请手动检查 questions.py 结构")