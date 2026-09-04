# -*- coding: utf-8 -*-
"""fix_df.py - 在 exec(safe_code) 前预定义 df = 真实数据兜底; 模块级缓存供图表复用。"""
import os, ast, shutil, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(BASE, "app", "services", "experiment_engine.py")

# ---- 前置：语法合法即可（已是"真实数据版"状态, 不动其它）----
s = open(P, encoding="utf-8", errors="ignore").read()
ast.parse(s)
print("[ok] 文件语法合法, lines =", len(s.splitlines()))

# 备份当前版本（可回滚）
shutil.copy(P, P + ".bak_df")
print("[ok] 已备份 -> experiment_engine.py.bak_df")

lines = s.split("\n")

# ========== 改动 A: 模块级缓存 _DATA_CACHE（插到 OUTPUT_ROOT 定义后）==========
anchor = None
for i, l in enumerate(lines):
    if l.startswith("OUTPUT_ROOT ="):
        anchor = i
        break
assert anchor is not None, "ERR: 找不到 OUTPUT_ROOT"
if "_DATA_CACHE" not in s:
    lines.insert(anchor + 1, "\n# [fix] run_id -> 真实 data_table 缓存\n_DATA_CACHE = {}")
    print("[A] 插入 _DATA_CACHE (L%d)" % (anchor + 2))
else:
    print("[A] _DATA_CACHE 已存在, 跳过")

# ========== 改动 B: run_experiment 拿到 data_table 后写入缓存 ==========
# 找到 "data_table = meta.get('data_table')" 那行, 在其后插入缓存写入
inserted = False
for i, l in enumerate(lines):
    if "data_table = meta.get('data_table')" in l:
        # 在该行后追加一行(保持同缩进)
        indent = l[:len(l) - len(l.lstrip())]
        lines.insert(i + 1, indent + "# [fix] 写入缓存供图表与 wrapper 使用\n" + indent + "_DATA_CACHE[str(run_id)] = data_table")
        inserted = True
        print("[B] run_experiment 写入缓存 (L%d)" % (i + 2))
        break
if not inserted:
    # 兜底: 找 "data_table = None" 处
    for i, l in enumerate(lines):
        if l.strip() == "data_table = None":
            indent = l[:len(l) - len(l.lstrip())]
            lines.insert(i + 1, indent + "_DATA_CACHE[str(run_id)] = data_table  # [fix]")
            inserted = True
            print("[B] 兜底: 在 'data_table = None' 后写入缓存 (L%d)" % (i + 2))
            break
assert inserted, "ERR: 找不到 data_table 赋值点, 请贴 run_experiment 完整文本"

# ========== 改动 C: 在 wrapper 的 "exec(" 前注入 df 定义 (8空格缩进) ==========
exec_idx = None
for i, l in enumerate(lines):
    if l.strip() == '"exec(\\"\\"\\"\\n':
        exec_idx = i
        break
if exec_idx is None:
    for i, l in enumerate(lines):
        if '"exec(' in l:
            exec_idx = i
            break
assert exec_idx is not None, "ERR: 找不到 exec 注入点"

INJECT = (
    '        # [fix] exec 前预定义 df = 真实数据, 避免用户代码 NameError\\n'
    '        df = None\\n'
    '        try:\\n'
    '            import pandas as _pd\\n'
    '            _dt = _DATA_CACHE.get(str(run_id), None)\\n'
    '            if _dt is None and \'data_table\' in globals():\\n'
    '                _dt = data_table\\n'
    '            if _dt is not None:\\n'
    '                if isinstance(_dt, dict) and "rows" in _dt:\\n'
    '                    df = _pd.DataFrame(_dt["rows"], columns=_dt.get("columns"))\\n'
    '                else:\\n'
    '                    df = _pd.DataFrame(_dt)\\n'
    '        except Exception as _e:\\n'
    '            df = None\\n'
    '            del _e\\n'
)
# 用 splitlines 构造多行, 每行带 8 空格前缀
inject_lines = [
    '        # [fix] exec 前预定义 df = 真实数据, 避免用户代码 NameError',
    '        df = None',
    '        try:',
    '            import pandas as _pd',
    '            _dt = _DATA_CACHE.get(str(run_id), None)',
    "            if _dt is None and 'data_table' in globals():",
    '                _dt = data_table',
    '            if _dt is not None:',
    '                if isinstance(_dt, dict) and "rows" in _dt:',
    '                    df = _pd.DataFrame(_dt["rows"], columns=_dt.get("columns"))',
    '                else:',
    '                    df = _pd.DataFrame(_dt)',
    '        except Exception as _e:',
    '            df = None',
    '            del _e',
]
if 'df = None' not in lines[exec_idx - 1]:
    lines = lines[:exec_idx] + inject_lines + lines[exec_idx:]
    print("[C] 在 L%d 前注入 df 定义 (%d 行)" % (exec_idx + 1, len(inject_lines)))
else:
    print("[C] df 定义已存在, 跳过")

# ========== 写回 + 校验 ==========
src = "\n".join(lines) + "\n"
ast.parse(src)   # 先校验, 不通过不写盘
with open(P, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
final = open(P, encoding="utf-8").read()
ast.parse(final)

print("\n[OK] 写入成功 + 语法 OK, lines =", len(final.splitlines()))
print("\n=== 复核 ===")
print("1) _DATA_CACHE 定义:", "_DATA_CACHE = {}" in final)
print("2) 缓存写入:", "_DATA_CACHE[str(run_id)] = data_table" in final)
print("3) df 定义注入:", "df = None" in final and "exec(" in final)
print("4) df 在 exec 前:", final.index("df = None") < final.index('safe_code +') if "safe_code +" in final else "N/A")
print("5) 图表仍是真实版:", "无真实数据, 跳过(不造假)" in final)
print("6) SYNTAX OK:", True)
