"""删除行621-632的重复PDF块及残留warning"""
from pathlib import Path

FILE = Path(__file__).parent / "app" / "api" / "v1" / "questions.py"
lines = FILE.read_text(encoding="utf-8").splitlines(keepends=True)

# 删除 621~632 (0-indexed: 620~631)
del lines[620:632]

FILE.write_text("".join(lines), encoding="utf-8")

count = sum(1 for l in lines if "PDF已生成(主交付物)" in l)
print("✅ 已删除12行，剩余标记数: %d" % count)