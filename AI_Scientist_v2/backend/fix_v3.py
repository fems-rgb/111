# -*- coding: utf-8 -*-
"""fix_v3.py - 序列化 data_table 进 safe_code 前端, exec 前还原 df。仅改 safe_code + 签名。"""
import os, ast, shutil, json as _json, subprocess, tempfile, sys

BASE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(BASE, "app", "services", "experiment_engine.py")

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
    print(f"[C] 删除模块层 _resolve_df L{r+1}..L{end}")

# D: _build_wrapper 签名加 data_table=None (精确整行替换)
sig = find_def("_build_wrapper")
assert sig >= 0
indent = lines[sig][:len(lines[sig]) - len(lines[sig].lstrip())]
if "data_table=None" not in lines[sig]:
    lines[sig] = indent + "def _build_wrapper(code: str, out_dir: str, charts_dir: str, generate_video: bool, data_table=None) -> str:"
    print("[D] 签名加 data_table=None")
else:
    print("[D] 签名已含, 跳过")

# E: 替换 safe_code 构造, 在用户代码前 prepend df 还原代码
sc = None
for i, l in enumerate(lines):
    if l.strip().startswith("safe_code = code.replace("):
        sc = i; break
assert sc is not None, "找不到 safe_code 行"
print(f"[E] safe_code @ L{sc+1}")

NEW_SC = (
    indent + "# [fix] 真实数据 -> df (在用户代码前, 由 exec 执行)\n"
    indent + "_serialized = _json.dumps(data_table, ensure_ascii=False, default=str) if data_table is not None else 'null'\n"
    indent + "_df_setup = (\n"
    indent + "    'import pandas as _pd\\n'\n"
    indent + "    '_dt = json.loads(' + repr(_serialized) + ')\\n'\n"
    indent + "    'df = None\\n'\n"
    indent + "    'if _dt is not None:\\n'\n"
    indent + "    '    try:\\n'\n"
    indent + "    '        if isinstance(_dt, dict) and \"rows\" in _dt:\\n'\n"
    indent + "    '            df = _pd.DataFrame(_dt[\"rows\"], columns=_dt.get(\"columns\"))\\n'\n"
    indent + "    '        else:\\n'\n"
    indent + "    '            df = _pd.DataFrame(_dt)\\n'\n"
    indent + "    '    except Exception:\\n'\n"
    indent + "    '        df = None\\n'\n"
    indent + ")\n"
    indent + "safe_code = _df_setup + code.replace(chr(92), chr(92)+chr(92)).replace(chr(34)*3, chr(34)+chr(39)+chr(34))"
).split("\n")
lines = lines[:sc] + NEW_SC + lines[sc + 1:]
print(f"[E] 已替换为 df 预设置 ({len(NEW_SC)} 行)")

# F: 调用处传 data_table=data_table
for i, l in enumerate(lines):
    if "_build_wrapper(code, out_dir, charts_dir, generate_video)" in l and "data_table" not in l:
        lines[i] = l.replace("generate_video)", "generate_video, data_table=data_table)")
        print(f"[F] 调用处 L{i+1} 传 data_table"); break
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
spec = importlib.util.spec_from_file_location("cem", P)
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
    if "_dt =" in l or "df = None" in l or "import pandas" in l or "DataFrame" in l:
        print(f"    L{i+1}: {l[:90]}")

r = subprocess.run([sys.executable, run], capture_output=True, text=True)
print("  STDOUT:", r.stdout.strip())
print("  STDERR:", (r.stderr.strip()[-400:] if r.stderr.strip() else "无"))
print("  rc:", r.returncode)

print("\n=== 复核 ===")
print("1) 签名含 data_table:", "data_table=None)" in final.splitlines()[sig] if sig < len(final.splitlines()) else "check")
print("2) _df_setup 注入:", "_df_setup = (" in final)
print("3) safe_code prepend:", "_serialized = _json.dumps(data_table" in final)
print("4) 调用传参:", "data_table=data_table" in final)
print("5) 无残留 _resolve_df:", "def _resolve_df" not in final and "df = _resolve_df()" not in final)
print("6) 图表真实版:", "无真实数据, 跳过(不造假)" in final)
print("7) SYNTAX OK:", True)
