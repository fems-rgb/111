# -*- coding: utf-8 -*-
"""fix_df2.py - 在 wrapper 字符串的 exec 前正确注入 df 定义（作为拼接片段）"""
import os, ast, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(BASE, "app", "services", "experiment_engine.py")

s = open(P, encoding="utf-8", errors="ignore").read()
ast.parse(s)
print("[ok] 文件语法合法, lines =", len(s.splitlines()))

# 备份
shutil.copy(P, P + ".bak_df2")
print("[ok] 备份 -> experiment_engine.py.bak_df2")

lines = s.split("\n")

# ========== A: 模块级缓存（若已有则跳过）==========
anchor = None
for i, l in enumerate(lines):
    if l.startswith("OUTPUT_ROOT ="):
        anchor = i
        break
assert anchor is not None
if "_DATA_CACHE" not in s:
    lines.insert(anchor + 1, "_DATA_CACHE = {}  # [fix] run_id -> 真实 data_table")
    print("[A] 插入 _DATA_CACHE")
else:
    print("[A] _DATA_CACHE 已存在, 跳过")

# ========== B: run_experiment 写入缓存 ==========
inserted = False
for i, l in enumerate(lines):
    if "data_table = meta.get('data_table')" in l:
        indent = l[:len(l) - len(l.lstrip())]
        lines.insert(i + 1, indent + "_DATA_CACHE[str(run_id)] = data_table  # [fix]")
        inserted = True
        print("[B] 写入缓存 (L%d)" % (i + 2)); break
if not inserted:
    for i, l in enumerate(lines):
        if l.strip() == "data_table = None":
            indent = l[:len(l) - len(l.lstrip())]
            lines.insert(i + 1, indent + "_DATA_CACHE[str(run_id)] = data_table  # [fix]")
            inserted = True
            print("[B] 兜底写入 (L%d)" % (i + 2)); break
assert inserted, "ERR: 找不到 data_table 赋值点"

# ========== C: 在 "exec(" 前注入 df 定义（关键修正）==========
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
assert exec_idx is not None, "ERR: 找不到 exec 点"

# 参考相邻片段的形态: L126 '"plt.show = _show\\n"' -> 前缀 '"'  后缀 '\\n"'
# 我们构造普通源码块(8空格缩进), 逐行包成 '"<line>\\n"'
SRC = '''        # [fix] exec 前确保 df 已定义(真实数据兜底)
        df = _resolve_df()
'''
resolve = '''    # [fix] 真实数据解析函数(模块级, wrapper 通过 globals 可见)
    def _resolve_df():
        _dt = _DATA_CACHE.get(str(run_id), None)
        if _dt is None and 'data_table' in globals():
            _dt = data_table
        if _dt is None:
            return None
        try:
            import pandas as _pd
            if isinstance(_dt, dict) and "rows" in _dt:
                return _pd.DataFrame(_dt["rows"], columns=_dt.get("columns"))
            return _pd.DataFrame(_dt)
        except Exception:
            return None
'''

def wrap(src):
    """把一段普通 python 源码(已含 8空格缩进)转成 wrapper 拼接片段列表"""
    out = []
    for raw in src.split("\n"):
        line = raw.rstrip("\n")
        if line.strip() == "":
            out.append('        ""  # 空行')
        else:
            # 转义内部的双引号, 加前缀 " 与后缀 \n"
            escaped = line.replace('"', '\\"')
            out.append('        "' + escaped + '\\n"')
    return out

inject = wrap(SRC)

# 去重: 若已注入则跳过
if 'df = _resolve_df()' not in s:
    lines = lines[:exec_idx] + inject + lines[exec_idx:]
    print("[C] 在 L%d 前注入 %d 个字符串片段" % (exec_idx + 1, len(inject)))
else:
    print("[C] df 注入已存在, 跳过")

# resolve 函数放在模块级(在 _build_wrapper 之前, 即 L33 之前)
if "def _resolve_df" not in s:
    # 找到 _build_wrapper 定义行
    bw = None
    for i, l in enumerate(lines):
        if l.startswith("def _build_wrapper"):
            bw = i
            break
    assert bw is not None
    # 插到 bw 这一行的前面(作为模块级函数)
    resolve_lines = [('    "' + x.replace('"', '\\"') + '\\n"') if False else x
                     for x in resolve.rstrip("\n").split("\n")]
    # 直接用普通行(模块级, 无引号包裹)
    lines = lines[:bw] + resolve.rstrip("\n").split("\n") + [""] + lines[bw:]
    print("[C2] 插入模块级 _resolve_df() (L%d 前)" % (bw + 1))

# ========== 写回 + 校验 ==========
src2 = "\n".join(lines) + "\n"
ast.parse(src2)   # ← 先校验; 不通过 = 不写盘
with open(P, "w", encoding="utf-8", newline="\n") as f:
    f.write(src2)
final = open(P, encoding="utf-8").read()
ast.parse(final)

print("\n[OK] 写入成功 + 语法 OK, lines =", len(final.splitlines()))
print("\n=== 复核 ===")
print("1) _DATA_CACHE:", "_DATA_CACHE = {}" in final)
print("2) 缓存写入:", "_DATA_CACHE[str(run_id)] = data_table" in final)
print("3) _resolve_df 定义:", "def _resolve_df" in final)
print("4) df 注入(exec 前):", "df = _resolve_df()" in final)
print("5) df 在 exec 前:", final.index("df = _resolve_df()") < final.index('safe_code +'))
print("6) 图表仍是真实版:", "无真实数据, 跳过(不造假)" in final)
print("7) SYNTAX OK:", True)
