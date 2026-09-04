# -*- coding: utf-8 -*-
"""fix_running.py - 修复 _exec: 异常时也必须写 run.status='failed' + commit,
   否则前端永远卡在 '运行中'。同时加兜底, 确保任何路径都能提交状态。"""
import os, re, ast, shutil

LAB = os.path.join(r"D:\111-1\AI_Scientist_v2\backend", "app", "api", "v1", "experiment_lab.py")
src = open(LAB, encoding="utf-8", errors="ignore").read()
ast.parse(src)
shutil.copy(LAB, LAB + ".running_bak")

lines = src.split("\n")

# ---- 定位 L132 except 块 (try 在 L77, except Exception as e 在 L132, 之后只有 logger.error) ----
# 找到 "except Exception as e:" 那行
exc_line = None
for i, l in enumerate(lines):
    if l.strip().startswith("except Exception as") and i > 70 and i < 135:
        # 确认它是 _exec 里的(后面紧跟 logger.error)
        if i+1 < len(lines) and "logger." in lines[i+1]:
            exc_line = i
            break
assert exc_line is not None, "找不到 except Exception (L132)"
print(f"[*] except 行 = L{exc_line+1}: {lines[exc_line].strip()}")

# 当前 L132-L133:
#   except Exception as e:
#       logger.error(f'...', exc_info=True)
# 在其后加: 写 failed 状态 + commit
indent = lines[exc_line+1][:len(lines[exc_line+1]) - len(lines[exc_line+1].lstrip())]
extra = [
    indent + "# [fix-running] 异常时必须持久化状态, 否则前端永远 '运行中'",
    indent + "try:",
    indent + "    if run is not None:",
    indent + "        run.status = 'failed'",
    indent + "        run.error_message = str(e)[:2000]",
    indent + "        run.completed_at = datetime.now(timezone.utc)",
    indent + "        await db.commit()",
    indent + "        print(f'[lab] _exec 异常已记录 run {run.id}: {e}')",
    indent + "except Exception as _commit_err:",
    indent + "    print(f'[lab] _exec 状态提交失败: {_commit_err}')",
]
# 插入到 except 块末尾: 找 except 块结束(下一个同级缩进或函数结束)
# except 块体缩进 = indent; 结束于缩进 < indent 的行或空行后的函数尾
insert_at = exc_line + 2  # 当前是 logger.error 那行之后
# 但要把 extra 插在 logger.error 之后; 直接插在 exc_line+2 即可(logger 在 exc_line+1)
lines = lines[:insert_at] + extra + lines[insert_at:]

new_src = "\n".join(lines) + "\n"
ast.parse(new_src)
open(LAB, "w", encoding="utf-8", newline="\n").write(new_src)
final = open(LAB, encoding="utf-8").read()
ast.parse(final)

print("[ok] _exec except 块已加固: 异常 -> run.status='failed' + commit")
print("\n=== 校验 ===")
import importlib.util
# 只校验语法(避免循环导入)
ast.parse(final)
print("SYNTAX OK:", True)
print("\n改动后 L130-L145:")
for i, l in enumerate(final.splitlines()):
    if 130 <= i+1 <= 145:
        print(f"  L{i+1}: {l}")
