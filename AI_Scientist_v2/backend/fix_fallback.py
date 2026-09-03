"""补回流水线PDF失败时的回退逻辑"""
from pathlib import Path

FILE = Path(__file__).parent / "app" / "api" / "v1" / "questions.py"
lines = FILE.read_text(encoding="utf-8").splitlines(keepends=True)

# 找到行619 (0-indexed=618) 的 else:
for i, l in enumerate(lines):
    if i >= 617 and i <= 621 and l.strip() == "else:" and "logger.info" in lines[i-1]:
        # 在这个 else: 后面插入回退代码
        indent = "                            "  # 与上面if块同级
        insert = [
            indent + "task.document_path = _report\n",
            indent + 'logger.warning("⚠️ 流水线PDF生成失败，回退为Markdown")\n',
        ]
        lines[i+1:i+1] = insert
        print("✅ 已在行 %d 后补回2行回退逻辑" % (i+2))
        break

FILE.write_text("".join(lines), encoding="utf-8")