# -*- coding: utf-8 -*-
"""_lib_auto_chart.py - 独立存放(真实数据版)。"""


def _auto_generate_charts(charts_dir: str, run_id, data_table=None):
    import os
    import numpy as np
    import pandas as _pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import logging
    logger = logging.getLogger(__name__)

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
        logger.warning("[autochart] run %s 无真实数据, 跳过(不造假)", run_id)
        return out

    nums = [c for c in df.columns if df[c].dtype.kind in "biufc"]
    if len(nums) >= 2:
        xc, yc = nums[0], nums[1]
        path = os.path.join(charts_dir, "relation.png")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(df[xc].astype(float).values, df[yc].astype(float).values, alpha=0.6)
        try:
            c = np.polyfit(df[xc].astype(float).values, df[yc].astype(float).values, 1)
            ax.plot(df[xc].astype(float).values,
                    c[0] * df[xc].astype(float).values + c[1], "r-", lw=2,
                    label="y=%.2fx+%.2f" % (c[0], c[1]))
        except Exception:
            pass
        ax.set_title("relation %s vs %s (run %s)" % (xc, yc, run_id))
        ax.set_xlabel(xc); ax.set_ylabel(yc); ax.legend()
        plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
        out.append(path)
    if nums:
        col = nums[0]
        path = os.path.join(charts_dir, "distribution.png")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(df[col].dropna().astype(float),
                bins=min(30, max(5, len(df) // 10)), density=True, alpha=0.7)
        ax.set_title("%s distribution (run %s)" % (col, run_id))
        ax.set_xlabel(col); ax.set_ylabel("density")
        plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
        out.append(path)
    if len(nums) >= 3:
        path = os.path.join(charts_dir, "correlation.png")
        fig, ax = plt.subplots(figsize=(6, 5))
        corr = df[nums].apply(_pd.to_numeric, errors="coerce").corr()
        im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(corr.columns)))
        ax.set_yticklabels(corr.columns, fontsize=8)
        fig.colorbar(im, ax=ax)
        ax.set_title("correlation matrix (run %s)" % run_id)
        plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
        out.append(path)
    logger.info("[autochart] run %s 真实数据生成 %d 张图", run_id, len(out))
    return out
