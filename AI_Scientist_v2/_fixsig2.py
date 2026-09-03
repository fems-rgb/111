p = "backend/app/agents/orchestrator.py"
src = open(p, encoding="utf-8").read()

print("="*64)
print("修改前 L39")
print("="*64)
lines = src.split("\n")
print("  L39|", lines[38].rstrip()[:160])

# 精确锚点：在 mode: str = "quick" 之后加 resume_mode
old = 'custom_pipeline: list[str] | None = None, mode: str = "quick") ->'
new = 'custom_pipeline: list[str] | None = None, mode: str = "quick", resume_mode: bool = False) ->'

if old in src:
    src = src.replace(old, new, 1)
    open(p, "w", encoding="utf-8").write(src)
    print("\n[OK] 签名已加 resume_mode: bool = False")
else:
    print("\n[WARN] 精确锚点未匹配，尝试宽松方式")
    # 宽松：找到 "mode: str = \"quick\"" 那行，在其后插入
    if 'mode: str = "quick"' in src:
        src = src.replace(
            'mode: str = "quick"',
            'mode: str = "quick", resume_mode: bool = False',
            1
        )
        open(p, "w", encoding="utf-8").write(src)
        print("[OK] 宽松方式已加 resume_mode")
    else:
        print("[错误] 未找到 mode 参数，当前签名:")
        print("  " + lines[38].rstrip())

import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[syntax] OK")
except py_compile.PyCompileError as e:
    print("[syntax] L%d: %s" % (e.lineno, e.msg))
