"""生成文件统一落盘位置 —— 固定根目录，与启动 cwd 无关

约定（唯一入口）：AI / 研究流水线 / 课件 / 实验 / PDF 的一切**产物**都必须经本模块
取路径，禁止再手写 ``os.path.join(os.getcwd(), "output", ...)`` 这类分散分支。

    backend/generated/                 ← GENERATED_ROOT（绝对、固定）
    ├── reports/<project_id>/              项目研究报告          report.md
    ├── questions/<task_id>/               科学问题报告          report.md
    ├── deliverables/project_<id>/         流水线交付物          report.pdf + charts/
    ├── pdf/                               PDF 导出              *.pdf
    ├── experiments/<run_id>/              实验模拟场沙箱输出    charts/ video/
    ├── courseware/c<g>/cw<id>/            课件逐页瘦身渲染图    s###.jpg
    ├── exports/                           课件反向导出          cw<id>_v<n>.pptx
    ├── agent_output/project_<id>/         Agent 工具写出的文件
    ├── tmp/external/                      外部文献采集临时件
    └── cache/literature/                  文献检索缓存          *.json

用户上传的**原始文件**不属于生成文件，仍在 backend/uploads/。

历史兼容：旧产物散落在 backend/output/* 与 backend/uploads/courses*，
所有读取统一走 :func:`resolve`，它按 generated → 旧根 的顺序探测，因此老数据不会 404。
"""
from __future__ import annotations

import os
from pathlib import Path

# backend/ 根（app/utils/paths.py → 上三级），不用 os.getcwd()，避免换目录启动就散落新文件
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
GENERATED_ROOT = BACKEND_ROOT / "generated"
UPLOADS_ROOT = BACKEND_ROOT / "uploads"
LOGS_ROOT = BACKEND_ROOT / "logs"

# kind → (generated 下的相对子目录, [旧根相对路径候选…])
# 旧根路径相对于 BACKEND_ROOT，仅供 resolve() 读取历史文件用；
# 注意旧路径本身带目录前缀（如 courses/c1/…），所以旧根写 uploads 而不是 uploads/courses
KINDS: dict[str, tuple[str, tuple[str, ...]]] = {
    "reports":        ("reports",        ("output",)),
    "questions":      ("questions",      ("output",)),
    "deliverables":   ("deliverables",   ("output",)),
    "pdf":            ("pdf",            ("output",)),
    "experiments":    ("experiments",    ("output",)),
    "courseware":     ("courseware",     ("uploads",)),
    "exports":        ("exports",        ("uploads",)),
    "agent_output":   ("agent_output",   ("uploads",)),
    "tmp":            ("tmp/external",   ("uploads",)),
    "cache":          ("cache/literature", ("output",)),
}

# 启动时预建的骨架目录（保证「地方固定」开箱即存在）
_SKELETON = ("reports", "questions", "deliverables", "pdf", "experiments",
             "courseware", "exports", "agent_output", "tmp/external", "cache/literature")


def _safe_parts(parts: tuple, kind: str) -> list[str]:
    """挡掉绝对路径与 .. —— 生成文件不允许写到 GENERATED_ROOT 之外"""
    out = []
    for p in parts:
        s = str(p).strip()
        if not s:
            continue
        if os.path.isabs(s) or ".." in Path(s).parts:
            raise ValueError(f"非法生成文件子路径: {s!r} (kind={kind})")
        out.extend(x for x in s.replace("\\", "/").split("/") if x not in ("", "."))
    return out


def kind_subdir(kind: str) -> str:
    try:
        return KINDS[kind][0]
    except KeyError:
        raise ValueError(f"未知生成文件类别: {kind!r}，可选：{', '.join(sorted(KINDS))}") from None


def peek_dir(kind: str, *parts) -> Path:
    """只算路径不建目录（清理 / 探测场景用，避免副产物建空目录）"""
    return GENERATED_ROOT.joinpath(kind_subdir(kind), *_safe_parts(parts, kind))


def gen_dir(kind: str, *parts) -> Path:
    """取（并创建）某类生成文件的目录，绝对路径"""
    d = GENERATED_ROOT.joinpath(kind_subdir(kind), *_safe_parts(parts, kind))
    d.mkdir(parents=True, exist_ok=True)
    return d


def gen_file(kind: str, *parts) -> Path:
    """取某类生成文件的落盘路径（父目录自动创建，文件名需带后缀）"""
    if not parts:
        raise ValueError("gen_file 需要文件名")
    *dirs, name = parts
    return gen_dir(kind, *dirs) / _safe_parts((name,), kind)[0]


def rel(kind: str, *parts) -> str:
    """相对 GENERATED_ROOT 的 posix 路径，适合入库（读取时交给 resolve）"""
    return "/".join([kind_subdir(kind), *_safe_parts(parts, kind)])


def _migrate_abs_tail(p: Path) -> Path | None:
    """绝对路径已失效时，把其中 output/… 或 uploads/… 的后缀映射回 backend 根重试
    （老库里 document_path 存的是当时 cwd 算出来的绝对路径）"""
    parts = [x for x in p.parts]
    for anchor in ("output", "uploads"):
        if anchor not in parts:
            continue
        i = len(parts) - 1 - parts[::-1].index(anchor)
        tail = Path(*parts[i:])
        cand = BACKEND_ROOT / tail
        if cand.exists():
            return cand
    return None


def resolve(stored: str | os.PathLike | None, kind: str | None = None) -> Path | None:
    """把数据库里存的路径解析成真实文件；找不到返回 None。

    探测顺序：绝对路径 → generated 根 → 该 kind 的旧根（output/… 或 uploads/…）。
    """
    if not stored:
        return None
    p = Path(str(stored))
    if p.is_absolute():
        return p if p.exists() else _migrate_abs_tail(p)
    cand: list[Path] = [GENERATED_ROOT / p]
    if kind:
        cand.append(GENERATED_ROOT / kind_subdir(kind) / p)
        for legacy in KINDS.get(kind, ("", ()))[1]:
            cand.append(BACKEND_ROOT / legacy / p)
    else:
        for legacy in (GENERATED_ROOT, BACKEND_ROOT / "output", UPLOADS_ROOT):
            cand.append(legacy / p)
    for c in cand:
        if c.exists():
            return c
    return None


def rel_from_backend(path: Path) -> str:
    """给人看的短路径（backend/generated/…）"""
    try:
        return path.relative_to(BACKEND_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def ensure_tree() -> Path:
    """建好固定骨架，并给每个叶子放 .gitkeep 以便目录结构入库"""
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    for sub in _SKELETON:
        d = GENERATED_ROOT / sub
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.touch()
    for root in (UPLOADS_ROOT, LOGS_ROOT):
        root.mkdir(parents=True, exist_ok=True)
    return GENERATED_ROOT


def tree_stat(limit_per_kind: int = 5) -> list[dict]:
    """按类别统计生成文件（启动日志 / 自检用）"""
    rows = []
    for kind, (sub, _) in KINDS.items():
        base = GENERATED_ROOT / sub
        files = [f for f in base.rglob("*") if f.is_file() and f.name != ".gitkeep"] if base.is_dir() else []
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        rows.append({
            "kind": kind,
            "dir": rel_from_backend(base),
            "count": len(files),
            "bytes": sum(f.stat().st_size for f in files),
            "latest": [f.name for f in files[:limit_per_kind]],
        })
    return rows
