# -*- coding: utf-8 -*-
"""[patch_chart v3] fix charts not matching: A) rewrite _auto_generate_charts (real data, no fake); B) inject df before exec. anchors + line-scan, all ASCII-safe."""
import os, re, shutil, py_compile

P = r"D:\111-1\AI_Scientist_v2\backend\app\services\experiment_engine.py"
BAK = P + ".bak_chart"
if not os.path.exists(BAK):
    shutil.copy(P, BAK); print("[backup] " + BAK)

lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

START = "# [AUTOCHART-START] do not edit"
END   = "# [AUTOCHART-END] do not edit"

# ---------- A) rewrite _auto_generate_charts body via line-scan ----------
def find(fn):
    for i, l in enumerate(lines):
        if l.startswith(fn):
            return i
    return -1

si = find("def _auto_generate_charts")
assert si >= 0, "ERR cannot find def _auto_generate_charts"
# scan forward for first '# [' marker (our anchor region) or next top-level def
start = None
for i in range(si, len(lines)):
    if START in lines[i]:
        start = i; break
if start is None:
    start = si  # no anchor yet; we will insert one right before the def-body

# find end anchor
end = None
for i in range(start + 1, len(lines)):
    if END in lines[i]:
        end = i + 1; break  # include END line
if end is None:
    # fallback: next top-level def/class after start
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("def ") or lines[i].startswith("async def ") or lines[i].startswith("class "):
            end = i; break

# new function body (ASCII only, single-quoted docstring to avoid '"""' clash)
NEW = '''def _auto_generate_charts(charts_dir, run_id, data_table=None):
    ''''''[fix-mismatch] use REAL data_table; return [] (no fake charts) when no data.''''''    import numpy as np
    import pandas as _pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def _to_df(src):
        if src is None:
            return None
        try:
            if isinstance(src, dict) and "rows" in src and "columns" in src:
                cols, rows = src["columns"], src["rows"]
                if rows and isinstance(rows[0], dict):
                    return _pd.DataFrame(rows)
                return _pd.DataFrame(rows, columns=cols)
            return _pd.DataFrame(src)
        except Exception:
            return None

    df = _to_df(data_table)
    os.makedirs(charts_dir, exist_ok=True)
    out = []
    if df is None or len(df) == 0:
        logger.warning("[autochart] run %s has no real data_table; skip (no fake chart)", run_id)
        return out

    _nums = [c for c in df.columns if df[c].dtype.kind in "biufc"]
    try:
        _seed = int(run_id)
    except Exception:
        _seed = abs(hash(str(run_id))) % 9999
    np.random.seed(_seed)

    if len(_nums) >= 2:
        xc, yc = _nums[0], _nums[1]
        path = os.path.join(charts_dir, "relation.png")
        fig, ax = plt.subplots(figsize=(6, 4))
        x = df[xc].astype(float).values
        y = df[yc].astype(float).values
        ax.scatter(x, y, alpha=0.6)
        try:
            c = np.polyfit(x, y, 1)
            ax.plot(x, np.polyval(c, x), "r-", lw=2, label="y=%.2fx+%.2f" % (c[0], c[1]))
        except Exception:
            pass
        ax.set_title("relation %s vs %s (run %s)" % (xc, yc, run_id))
        ax.set_xlabel(xc); ax.set_ylabel(yc); ax.legend()
        plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
        out.append(path)

    if _nums:
        col = _nums[0]
        path = os.path.join(charts_dir, "distribution.png")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(df[col].dropna().astype(float), bins=min(30, max(5, len(df) // 10)), density=True, alpha=0.7, color="steelblue")
        ax.set_title("%s distribution (run %s)" % (col, run_id))
        ax.set_xlabel(col); ax.set_ylabel("density")
        plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
        out.append(path)

    if len(_nums) >= 3:
        path = os.path.join(charts_dir, "correlation.png")
        fig, ax = plt.subplots(figsize=(6, 5))
        corr = df[_nums].apply(_pd.to_numeric, errors="coerce").corr()
        im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(corr.columns)))
        ax.set_yticklabels(corr.columns, fontsize=8)
        fig.colorbar(im, ax=ax)
        ax.set_title("correlation matrix (run %s)" % run_id)
        plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
        out.append(path)

    logger.info("[autochart] run %s generated %d chart(s) from REAL data", run_id, len(out))
    return out
'''.split("\n")

print("[A] replace L%d..L%d (old _auto_generate_charts) -> real-data version" % (start + 1, end))
lines = lines[:start] + [START, ""] + NEW + ["", END] + lines[end:]
src = "\n".join(lines) + "\n"

# ---------- B1) add data_table param to signatures ----------
def add_param(pat, name, flags=0):
    global src
    m = re.search(pat, src, flags)
    if not m:
        print("  [!] signature not matched (optional): " + pat)
        return
    head = m.group(0)
    if name in head:
        print("  [skip] " + name + " already present")
        return
    new_head = head.rstrip()[:-1].rstrip(",") + ", " + name + "):"
    src = src.replace(head, new_head, 1)
    print("  [ok] signature += " + name)

add_param(r"def _build_wrapper\([^)]*\):", "data_table=None")
add_param(r"async def run_experiment\(.*?\):\s*\n", "data_table=None", re.DOTALL)

# ---------- B2) update the call site ----------
oldcall = "_build_wrapper(code, out_dir, charts_dir, generate_video)"
newcall = oldcall + ", data_table=data_table"
if oldcall in src:
    src = src.replace(oldcall, newcall, 1)
    print("  [ok] call += data_table=data_table")
else:
    print("  [!] call site not matched; please add data_table=data_table manually")

# ---------- B3) inject df-setup right before exec("" ----------
INJECT = '''
# [fix-mismatch] ensure df is defined before exec (real data: data_table > result_data > files)
import pandas as _pdf, glob as _gdf, os as _odf
def _make_df():
    for _name in ("data_table", "result_data"):
        if _name in globals() and globals()[_name] is not None:
            try:
                return _pdf.DataFrame(globals()[_name])
            except Exception:
                pass
    for _c in list(_gdf.glob(_odf.path.join(_OUT, "*.csv"))) + list(_gdf.glob(_odf.path.join(_OUT, "*.json"))):
        try:
            if _c.endswith(".csv"):
                return _pdf.read_csv(_c)
            return _pdf.DataFrame(_pdf.read_json(_c).to_dict("records"))
        except Exception:
            pass
    return None
df = _make_df()
'''
ll = src.split("\n")
idx = None
for i, l in enumerate(ll):
    if '"exec("""' in l or '"exec(\\""' in l:
        idx = i; break
assert idx is not None, "ERR cannot find exec(\"\"\" injection point"
ll.insert(idx, INJECT.rstrip("\n"))
print("  [ok] injected df-setup before exec (L%d)" % (idx + 1))
src = "\n".join(ll) + "\n"

# ---------- write + compile check ----------
open(P, "w", encoding="utf-8").write(src)
py_compile.compile(P, doraise=True)
print("\n[ok] all edits applied + syntax OK")

# ---------- review ----------
out = open(P, encoding="utf-8").read().split("\n")
print("\n=== review ===")
for i, l in enumerate(out):
    if any(k in l for k in ["def _auto_generate_charts", START, END,
                             "no fake chart", "def _build_wrapper",
                             "async def run_experiment", "df = _make_df",
                             "_build_wrapper(code, out_dir"]):
        print("L%d| %s" % (i + 1, l.rstrip()[:220]))
