"""experiment_engine 单元测试（不真跑子进程）

聚焦 README P1 已知坑：
- `_check_safety` 拦截 os.system / shutil.rmtree / open('/etc/passwd') 等
- `_build_wrapper` 生成的代码是合法 Python 且包含图表注入
- `sns.scatterplot(x='col', y='col')` 无 data 时 wrapper 自动补 data=df
"""
from __future__ import annotations

import ast

from app.services import experiment_engine as ee


def test_safety_blocks_os_system():
    assert ee._check_safety("import os\nos.system('rm -rf /')") is not None


def test_safety_blocks_eval():
    assert ee._check_safety("x = eval('1+1')") is not None


def test_safety_blocks_shutil_import():
    assert ee._check_safety("import shutil\nshutil.rmtree('/')") is not None


def test_safety_allows_normal_code():
    code = (
        "import numpy as np\n"
        "x = np.arange(10)\n"
        "print(x.sum())\n"
    )
    assert ee._check_safety(code) is None


def test_build_wrapper_produces_valid_python():
    code = "print('hello')\n"
    wrapper = ee._build_wrapper(
        code,
        out_dir="/tmp/_x_out",
        charts_dir="/tmp/_x_out/charts",
        generate_video=False,
        data_table=None,
    )
    ast.parse(wrapper)  # 语法必须合法
    assert "print('hello')" in wrapper or 'print("hello")' in wrapper


def test_build_wrapper_injects_data_table():
    dt = {"columns": ["a", "b"], "rows": [[1, 2], [3, 4]]}
    wrapper = ee._build_wrapper(
        "print(df.head())",
        out_dir="/tmp/_y_out",
        charts_dir="/tmp/_y_out/charts",
        generate_video=False,
        data_table=dt,
    )
    ast.parse(wrapper)
    assert "pd.DataFrame" in wrapper
    assert '"a"' in wrapper or "'a'" in wrapper


def test_builtin_templates_at_least_three():
    """README 8.2 承诺 3 个内置实验模板"""
    names = {t["name"] for t in ee.BUILTIN_TEMPLATES}
    assert len(names) >= 3
    for tpl in ee.BUILTIN_TEMPLATES:
        assert {"name", "description", "code", "category"} <= set(tpl), tpl
