# -*- coding: utf-8 -*-
"""gen_apply.py : 生成 apply_patch.py (函数体用 chr(39) 拼, 无引号歧义)"""
import os

S = os.path.join(os.path.dirname(__file__), "apply_patch.py")

Q = chr(39) * 3            # 物理 '''
EMPTY_DOC = Q + " " + Q    # ''' '''
START = "# [AUTOCHART-START] do not edit"
END = "# [AUTOCHART-END] do not edit"

def body():
    L = []
    def w(s=""):
        L.append(s)
    w("def _auto_generate_charts(charts_dir, run_id, data_table=None):")
    w(EMPTY_DOC)
    w("    import numpy as np")
    w("    import pandas as _pd")
    w("    import matplotlib")
    w('    matplotlib.use("Agg")')
    w("    import matplotlib.pyplot as plt")
    w("")
    w("    def _to_df(src):")
    w("        if src is None:")
    w("            return None")
    w("        try:")
    w('            if isinstance(src, dict) and "rows" in src and "columns" in src:')
    w("                cols, rows = src['columns'], src['rows']")
    w("                if rows and isinstance(rows[0], dict):")
    w("                    return _pd.DataFrame(rows)")
    w("                return _pd.DataFrame(rows, columns=cols)")
    w("            return _pd.DataFrame(src)")
    w("        except Exception:")
    w("            return None")
    w("")
    w("    df = _to_df(data_table)")
    w("    os.makedirs(charts_dir, exist_ok=True)")
    w("    out = []")
    w("    if df is None or len(df) == 0:")
    w('        logger.warning("[autochart] run %s no real data_table; skip (no fake chart)", run_id)')
    w("        return out")
    w("")
    w('    _nums = [c for c in df.columns if df[c].dtype.kind in "biufc"]')
    w("    try:")
    w("        _seed = int(run_id)")
    w("    except Exception:")
    w("        _seed = abs(hash(str(run_id))) % 9999")
    w("    np.random.seed(_seed)")
    w("")
    w("    if len(_nums) >= 2:")
    w("        xc, yc = _nums[0], _nums[1]")
    w('        path = os.path.join(charts_dir, "relation.png")')
    w("        fig, ax = plt.subplots(figsize=(6, 4))")
    w("        x = df[xc].astype(float).values")
    w("        y = df[yc].astype(float).values")
    w("        ax.scatter(x, y, alpha=0.6)")
    w("        try:")
    w("            c = np.polyfit(x, y, 1)")
    w('            ax.plot(x, np.polyval(c, x), "r-", lw=2, label="y=%.2fx+%.2f" % (c[0], c[1]))')
    w("        except Exception:")
    w("            pass")
    w('        ax.set_title("relation %s vs %s (run %s)" % (xc, yc, run_id))')
    w("        ax.set_xlabel(xc); ax.set_ylabel(yc); ax.legend()")
    w('        plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()')
    w("        out.append(path)")
    w("")
    w("    if _nums:")
    w("        col = _nums[0]")
    w('        path = os.path.join(charts_dir, "distribution.png")')
    w("        fig, ax = plt.subplots(figsize=(6, 4))")
    w("        ax.hist(df[col].dropna().astype(float), bins=min(30, max(5, len(df) // 10)), density=True, alpha=0.7, color='steelblue')")
    w('        ax.set_title("%s distribution (run %s)" % (col, run_id))')
    w("        ax.set_xlabel(col); ax.set_ylabel('density')")
    w('        plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()')
    w("        out.append(path)")
    w("")
    w("    if len(_nums) >= 3:")
    w('        path = os.path.join(charts_dir, "correlation.png")')
    w("        fig, ax = plt.subplots(figsize=(6, 5))")
    w("        corr = df[_nums].apply(_pd.to_numeric, errors='coerce').corr()")
    w('        im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)')
    w("        ax.set_xticks(range(len(corr.columns)))")
    w("        ax.set_xticklabels(corr.columns, rotation=45, ha='right', fontsize=8)")
    w("        ax.set_yticks(range(len(corr.columns)))")
    w("        ax.set_yticklabels(corr.columns, fontsize=8)")
    w("        fig.colorbar(im, ax=ax)")
    w('        ax.set_title("correlation matrix (run %s)" % run_id)')
    w('        plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()')
    w("        out.append(path)")
    w("")
    w('    logger.info("[autochart] run %s generated %d chart(s) from REAL data", run_id, len(out))')
    w("    return out")
    return "\n".join(L)

apply = r'''# -*- coding: utf-8 -*-
"""apply_patch.py : 由 gen_apply.py 生成. 修图表货不对板."""
import os, re, shutil, py_compile, ast

P = os.path.join(os.path.dirname(__file__), "app", "services", "experiment_engine.py")
BAK = P + ".bak_chart"
if not os.path.exists(BAK):
    shutil.copy(P, BAK)
    print("[backup] " + BAK)

lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
START = "# [AUTOCHART-START] do not edit"
END = "# [AUTOCHART-END] do not edit"

NEW_BODY = __NEW_BODY__.split("\n")

# ---- A) 用锚点包裹 _auto_generate_charts ----
def find_def():
    for i, l in enumerate(lines):
        if l.startswith("def _auto_generate_charts"):
            return i
    return -1

si = find_def()
assert si >= 0, "ERR: def _auto_generate_charts not found"

# 若已有锚点(重跑), 找到锚点区间; 否则用下一个顶层 def 作 end
has_anchor = any(START in l for l in lines)
if has_anchor:
    a = next(i for i, l in enumerate(lines) if START in l)
    b = next(i for i, l in enumerate(lines) if END in l) + 1
    start, end = a, b
else:
    start = si
    end = len(lines)
    for i in range(si + 1, len(lines)):
        if lines[i].startswith("def ") or lines[i].startswith("async def ") or lines[i].startswith("class "):
            end = i
            break

# 校验: 旧函数确实在被替换区间内 (防御, 避免误删)
OLD_SIGNATURE = "def _auto_generate_charts(charts_dir: str, run_id, data_table=None):"
assert OLD_SIGNATURE in "\n".join(lines[start:end]), "ERR: old function body not matched; abort"

lines = lines[:start] + [START, ""] + NEW_BODY + ["", END] + lines[end:]
print("[A] _auto_generate_charts -> real-data version (L%d..L%d)" % (start + 1, end))
src = "\n".join(lines) + "\n"

# ---- B1) 签名 + data_table=None (兼容已存在的参数) ----
def add_param(pattern, new_param, flags=0):
    global src
    m = re.search(pattern, src, flags)
    if not m:
        print("  [!] signature not matched: " + pattern)
        return
    head = m.group(0)
    name = new_param.split("=")[0].strip()
    if name in head:
        print("  [skip] " + name + " already present")
        return
    # 去掉可能的返回类型注解, 在 '(' 后重拼
    body_ = head[head.index("(")+1 : head.rindex(")")]
    new_head = head[:head.index("(")+1] + body_.rstrip(", ").strip() + ", " + new_param + "):"
    src = src.replace(head, new_head, 1)
    print("  [ok] signature += " + name)

add_param(r"def _build_wrapper\([^)]*\):\s*\n", "data_table=None")
add_param(r"async def run_experiment\(.*?\):\s*\n", "data_table=None", re.DOTALL)

# ---- B2) 调用处 ----
oldcall = "_build_wrapper(code, out_dir, charts_dir, generate_video)"
if oldcall in src:
    src = src.replace(oldcall, oldcall + ", data_table=data_table", 1)
    print("  [ok] call += data_table=data_table")
else:
    print("  [!] call site not matched; add data_table=data_table by hand")

# ---- B3) 在 exec( 前注入 df-setup (行级查找, 不依赖转义) ----
INJECT = (
    "\n"
    "# [fix] df = 真实数据: data_table > result_data > out_dir 数据文件\n"
    "import pandas as _pdf, glob as _gdf, os as _odf\n"
    "def _make_df():\n"
    "    for _name in ('data_table', 'result_data'):\n"
    "        if _name in globals() and globals()[_name] is not None:\n"
    "            try: return _pdf.DataFrame(globals()[_name])\n"
    "            except Exception: pass\n"
    "    for _c in list(_gdf.glob(_odf.path.join(_OUT, '*.csv'))) + list(_gdf.glob(_odf.path.join(_OUT, '*.json'))):\n"
    "        try:\n"
    "            if _c.endswith('.csv'): return _pdf.read_csv(_c)\n"
    "            return _pdf.DataFrame(_pdf.read_json(_c).to_dict('records'))\n"
    "        except Exception: pass\n"
    "    return None\n"
    "df = _make_df()\n"
)
ll = src.split("\n")
idx = None
for i, l in enumerate(ll):
    if '"exec(' in l and l.strip().endswith(')'):   # wrapper 构建行:  "...", "exec(\"\"\"\n" + ...
        idx = i
        break
assert idx is not None, "ERR: cannot find `exec(` injection point"
ll.insert(idx, INJECT.rstrip("\n"))
print("  [ok] injected df-setup before exec (L%d)" % (idx + 1))
src = "\n".join(ll) + "\n"

# ---- 写回 + 语法校验 ----
open(P, "w", encoding="utf-8").write(src)
ast.parse(src)                       # 比 py_compile 更直接
print("\n[ok] all edits applied + syntax OK (ast.parse passed)")

# ---- 复核 ----
out = open(P, encoding="utf-8").read().split("\n")
print("\n=== review ===")
for i, l in enumerate(out):
    if any(k in l for k in ["def _auto_generate_charts", START, END,
                            "no fake chart", "def _build_wrapper",
                            "async def run_experiment", "df = _make_df",
                            "_build_wrapper(code, out_dir"]):
        print("L%d| %s" % (i + 1, l.rstrip()[:200]))
'''

apply = apply.replace("__NEW_BODY__", repr(body())[1:-1])  # 把函数体以安全字符串塞进去

with open(S, "w", encoding="utf-8") as f:
    f.write(apply)

# 自检: apply_patch.py 自己能编译
py_compile.compile(S, doraise=True)
print("[gen] wrote", S)
print("[gen] self-check: syntax OK")
