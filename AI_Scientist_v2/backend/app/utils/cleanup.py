# -*- coding: utf-8 -*-
"""统一资源清理工具：删除任务/项目时联动清理所有相关资源"""
import os
import shutil
from pathlib import Path


def _safe_remove(path_str: str):
    """安全删除一个文件或目录（路径可以是绝对或相对）"""
    if not path_str:
        return
    p = Path(path_str)
    if not p.is_absolute():
        p = Path(os.getcwd()) / p
    try:
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink()
    except Exception:
        pass


def clean_task_files(task_id: int, document_path: str = None):
    """清理任务相关的物理文件"""
    _safe_remove(document_path)
    # pdf_reports 里含 task_id 的文件
    pdf_dir = Path("output/pdf_reports")
    if pdf_dir.exists():
        for f in pdf_dir.iterdir():
            if f.is_file() and str(task_id) in f.name:
                _safe_remove(str(f))


def clean_project_files(project_id: int):
    """清理项目相关的物理文件"""
    _safe_remove(f"output/{project_id}")
    pdf_dir = Path("output/pdf_reports")
    if pdf_dir.exists():
        for f in pdf_dir.iterdir():
            if f.is_file() and f"project_{project_id}" in f.name:
                _safe_remove(str(f))
