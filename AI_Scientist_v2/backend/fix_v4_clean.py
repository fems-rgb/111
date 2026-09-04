# -*- coding: utf-8 -*-
"""fix_v4.py - 序列化 data_table 进 safe_code 前端, exec 前还原 df。

已通过沙盒端到端验证:
  data_table -> JSON -> _run.py 里 json.loads -> df = DataFrame(真实数据)
  用户代码可直接使用 df, 不再 NameError。

仅改动:
  A) 模块级 _DATA_CACHE (供图表复用真实数据)
  B) run_experiment 写缓存 (供 _auto_generate_charts)
  C) 删除残留 _resolve_df
  D) _build_wrapper 签名加 data_table=None
  E) safe_code = _df_setup + 用户代码  (_df_setup 在 exec 前还原 df)
  F) 调用处传 data_table=data_table
"""
import os, ast, shutil, json as _json, subprocess, tempfile, sys

BASE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(BASE, "app", "services", "experiment_engine.py")

if not os.path.exists(P + ".bak_df2"):
    print("[ERR] 缺少 experiment_engine.py.bak_df2, 请确认在 backend 目录下")
    sys.exit(1)

# ---- 从干净态(图表已是真实版)开始 ----
shutil.copy(P + ".bak_df2", P)
s = open(P, encoding="utf-8", errors="ignore").read()
ast.parse(s)
print("[ok] 回到干净态 bak_df2, lines =", len(s.splitlines()))
lines = s.split("\n")

def find_def(name):
    for i, l in enumerate(lines):
        if l.startswith("def " + name + "("):
            return i
    return -1

# A: 模块缓存(供 _auto_generate_charts 复用真实数据)
if "_DATA_CACHE" not in s:
    for i, l in enumerate(lines):
        if l.startswith("OUTPUT_ROOT ="):
            lines.insert(i + 1, "_DATA_CACHE = {}  # [fix] run_id -> data_table")
            print("[A] _DATA_CACHE 插入"); break

# B: run_experiment 写缓存(供图表)
for i, l in enumerate(lines):
    if "data_table = meta.get('data_table')" in l:
        ind = l[:len(l) - len(l.lstrip())]
        if not any("_DATA_CACHE[str(run_id)]" in x for x in lines):
            lines.insert(i + 1, ind + "_DATA_CACHE[str(run_id)] = data_table  # [fix]")
            print("[B] 缓存写入插入")
        break

# C: 删除所有残留的 _resolve_df(模块层 + wrapper 内的调用)
lines = [l for l in lines if "df = _resolve_df()" not in l.strip()]
r = find_def("_resolve_df")
if r >= 0:
    end = r + 1
    while end < len(lines) and (lines[end].startswith(" ") or lines[end].strip() == ""):
        end += 1
    lines = lines[:r] + lines[end:]
    print("[C] 删除模块层 _resolve_df L%d..L%d" % (r + 1, end))

# D: _build_wrapper 签名加 data_table=None (精确整行替换)
sig = find_def("_build_wrapper")
assert sig >= 0, "找不到 _build_wrapper"
if "data_table=None" not in lines[sig]:
    indent = lines[sig][:len(lines[sig]) - len(lines[sig].lstrip())]
    lines[sig] = indent + "def _build_wrapper(code: str, out_dir: str, charts_dir: str, generate_video: bool, data_table=None) -> str:"
    print("[D] 签名加 data_table=None")
else:
    print("[D] 签名已含, 跳过")

# E: 替换 safe_code 构造, 在用户代码前 prepend df 还原代码
#    用列表逐行构造, 缩进以 safe_code 原行为基准(避免层级错位)
sc = None
for i, l in enumerate(lines):
    if l.strip().startswith("safe_code = code.replace("):
        sc = i; break
assert sc is not None, "找不到 safe_code 行"
print("[E] safe_code @ L%d" % (sc + 1))

body = []
_bi = lines[sc][:len(lines[sc]) - len(lines[sc].lstrip())]  # 原行缩进
def a(x):
    body.append(_bi + x)
a("# [fix] 真实数据 -> df (在用户代码前, 由 exec 执行)")
a("_serialized = _json.dumps(data_table, ensure_ascii=False, default=str) if data_table is not None else 'null'")
a("_df_lines = []")
a("_df_lines.append('import json, pandas as _pd')")
a('''_df_lines.append('_dt = json.loads(' + repr(_serialized) + ')' )''')
a("_df_lines.append('df = None')")
a("_df_lines.append('if _dt is not None:')")
a("_df_lines.append('    try:')")
a('''_df_lines.append('        if isinstance(_dt, dict) and "rows" in _dt:' )''')
a('_df_lines.append(\'            df = _pd.DataFrame(_dt["rows"], columns=_dt.get("columns"))\')')
a("_df_lines.append('        else:')")
a("_df_lines.append('            df = _pd.DataFrame(_dt)')")
a("_df_lines.append('    except Exception:')")
a("_df_lines.append('        df = None')")
a("_df_setup = '\\n'.join(_df_lines) + '\\n'")
a("safe_code = _df_setup + code.replace(chr(92), chr(92)+chr(92)).replace(chr(34)*3, chr(34)+chr(39)+chr(34))")

lines = lines[:sc] + body + lines[sc + 1:]
print("[E] 已替换为 df 预设置 (%d 行)" % len(body))

# F: 调用处传 data_table=data_table
for i, l in enumerate(lines):
    if "_build_wrapper(code, out_dir, charts_dir, generate_video)" in l and "data_table" not in l:
        lines[i] = l.replace("generate_video)", "generate_video, data_table=data_table)")
        print("[F] 调用处 L%d 传 data_table" % (i + 1))
        break
else:
    print("[F] 调用处已传或无需改")

# ===== 写回 + 校验 =====
src = "\n".join(lines) + "\n"
ast.parse(src)   # 不通过不写盘
with open(P, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
final = open(P, encoding="utf-8").read()
ast.parse(final)
print("\n[OK] 写入成功, lines =", len(final.splitlines()))

# ===== 自测: 直接生成 wrapper 并运行, 验证 df = 真实数据 =====
print("\n=== 自测(生成 _run.py 并运行) ===")
import importlib.util
spec = importlib.util.spec_from_file_location("cem_test", P)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

w = mod._build_wrapper(
    "print('DF:', type(df).__name__)\\nif df is not None: print('COLS:', list(df.columns))",
    tempfile.mkdtemp(), tempfile.mkdtemp(), False,
    data_table={"columns": ["x", "y"], "rows": [[1, 2], [3, 4], [5, 6]]},
)
run = os.path.join(tempfile.mkdtemp(), "_run.py")
open(run, "w", encoding="utf-8").write(w)
rr = open(run, encoding="utf-8").read().splitlines()
print("  _run.py 中 df 相关行(节选):")
for i, l in enumerate(rr):
    if "_dt = json.loads" in l or "df = None" in l or "import json" in l or "DataFrame" in l:
        print("    L%d: %s" % (i + 1, l[:100]))

r = subprocess.run([sys.executable, run], capture_output=True, text=True)
print("  STDOUT:", r.stdout.strip())
print("  STDERR:", (r.stderr.strip()[-400:] if r.stderr.strip() else "无"))
print("  rc:", r.returncode)

print("\n=== 复核 ===")
print("1) 签名含 data_table:", "data_table=None)" in final.splitlines()[sig])
print("2) _df_setup 注入:", "_df_setup = '\\n'.join(_df_lines)" in final)
print("3) safe_code prepend:", "_serialized = _json.dumps(data_table" in final)
print("4) 调用传参:", "data_table=data_table" in final)
print("5) 无残留 _resolve_df:", ("def _resolve_df" not in final) and ("df = _resolve_df()" not in final))
print("6) 图表真实版:", "无真实数据, 跳过(不造假)" in final)
print("7) SYNTAX OK:", True)
