# -*- coding: utf-8 -*-
"""统一资源清理工具：删除任务/项目时联动清理所有相关生成文件

生成文件一律在固定根 backend/generated/（见 app/utils/paths.py），
本模块同时兜底清理历史遗留的 backend/output/ 目录。
"""
import os
import shutil
from pathlib import Path

from app.utils import paths


def _safe_remove(path_str: str | Path | None):
    """安全删除一个文件或目录（相对路径按 generated 根解析，兼容历史 output/ 根）"""
    if not path_str:
        return
    p = Path(str(path_str))
    if not p.is_absolute():
        p = paths.resolve(str(path_str)) or (paths.GENERATED_ROOT / p)
    try:
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink()
    except Exception:
        pass


def _rm_named(dir_path: Path, needle: str):
    """按文件名包含关系清理某个生成目录"""
    if not dir_path.is_dir():
        return
    for f in dir_path.iterdir():
        if f.is_file() and needle in f.name:
            _safe_remove(f)


def clean_task_files(task_id: int, document_path: str = None):
    """清理任务相关的物理文件"""
    _safe_remove(document_path)
    _safe_remove(paths.peek_dir("questions", str(task_id)))
    _rm_named(paths.peek_dir("pdf"), str(task_id))
    _rm_named(paths.BACKEND_ROOT / "output" / "pdf_reports", str(task_id))


def clean_project_files(project_id: int):
    """清理项目相关的物理文件（报告 / 交付物 / Agent 产物 / PDF）"""
    _safe_remove(paths.BACKEND_ROOT / "output" / str(project_id))  # 历史
    _safe_remove(paths.peek_dir("reports", str(project_id)))
    _safe_remove(paths.peek_dir("deliverables", f"project_{project_id}"))
    _safe_remove(paths.peek_dir("agent_output", f"project_{project_id}"))
    _rm_named(paths.peek_dir("pdf"), f"project_{project_id}")
    _rm_named(paths.BACKEND_ROOT / "output" / "pdf_reports", f"project_{project_id}")
