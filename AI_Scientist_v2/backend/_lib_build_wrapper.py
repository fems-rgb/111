# -*- coding: utf-8 -*-
"""_lib_build_wrapper.py - 独立存放, 由 apply 脚本 import 复用。"""


def _serialize_data_table(data_table) -> str:
    if data_table is None:
        return "'__NONE__'"
    try:
        s = __import__('json').dumps(data_table, ensure_ascii=False, default=str)
    except Exception:
        return "'__NONE__'"
    return repr(s)


def _build_wrapper(code: str, out_dir: str, charts_dir: str,
                   generate_video: bool, data_table=None) -> str:
    safe_code = (code
                 .replace(chr(92), chr(92) + chr(92))
                 .replace(chr(34) * 3, chr(34) + chr(39) + chr(34)))

    df_json = _serialize_data_table(data_table)

    anim = ""
    if generate_video:
        anim = (
            "\n"
            "# === Animation auto-save ===\n"
            "import atexit\n"
            "_ANIMS = []\n"
            "_orig_FA = getattr(animation, 'FuncAnimation', None)\n"
            "if _orig_FA is not None:\n"
            "    class _TA(_orig_FA):\n"
            "        def __init__(self, *a, **kw):\n"
            "            super().__init__(*a, **kw)\n"
            "            _ANIMS.append(self)\n"
            "    animation.FuncAnimation = _TA\n"
        )

    wrapper = (
        "# -*- coding: utf-8 -*-\n"
        "import sys, io, os, json, warnings\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "import matplotlib\n"
        "import matplotlib.pyplot as plt\n"
        "import matplotlib.animation as animation\n"
        "matplotlib.use('Agg')\n"
        "warnings.filterwarnings('ignore', category=UserWarning)\n"
        "sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')\n"
        "sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')\n"
        "\n"
        "OUT = r'" + out_dir.replace("'", "''") + "'\n"
        "CDIR = r'" + charts_dir.replace("'", "''") + "'\n"
        "_CHARTS = []\n"
        "\n"
        "_DF_JSON = " + df_json + "\n"
        "\n"
        "# === 图表捕获 ===\n"
        "_orig_savefig = plt.savefig\n"
        "def _save(*a, **kw):\n"
        "    if a:\n"
        "        p = a[0]\n"
        "        if not os.path.isabs(str(p)):\n"
        "            p = os.path.join(CDIR, str(p))\n"
        "        a = (p,) + a[1:]\n"
        "    kw.setdefault('dpi', 150)\n"
        "    kw.setdefault('bbox_inches', 'tight')\n"
        "    _orig_savefig(*a, **kw)\n"
        "    _CHARTS.append(str(a[0]) if a else '')\n"
        "plt.savefig = _save\n"
        "\n"
        "_orig_show = plt.show\n"
        "def _show(*a, **kw):\n"
        "    import glob as _glb, os as _os\n"
        "    _st = set(_CHARTS)\n"
        "    for _f in sorted(_glb.glob(_os.path.join(CDIR, '*.png'))):\n"
        "        if _f not in _st:\n"
        "            _CHARTS.append(_f)\n"
        "            _st.add(_f)\n"
        "    plt.close('all')\n"
        "plt.show = _show\n"
        + anim +
        "\n"
        "def __run(__code):\n"
        "    import builtins\n"
        "    try:\n"
        "        _dt = None if _DF_JSON == '__NONE__' else json.loads(_DF_JSON)\n"
        "    except Exception:\n"
        "        _dt = None\n"
        "    df = None\n"
        "    if _dt is not None:\n"
        "        try:\n"
        "            if isinstance(_dt, dict) and 'rows' in _dt:\n"
        "                df = pd.DataFrame(_dt['rows'], columns=_dt.get('columns'))\n"
        "            else:\n"
        "                df = pd.DataFrame(_dt)\n"
        "        except Exception:\n"
        "            df = None\n"
        "    _ns = {'__builtins__': builtins, 'df': df,\n"
        "           'pd': pd, 'np': np, 'plt': plt, 'os': os, 'json': json}\n"
        "    exec(__code, _ns)\n"
        "    if 'result_data' in _ns:\n"
        "        globals()['result_data'] = _ns['result_data']\n"
        "\n"
        "__USER_CODE = (\n"
        '    r"""\n'
        + safe_code +
        '\n"""\n'
        ")\n"
        "\n"
        "__run(__USER_CODE)\n"
        "\n"
        "_result = {'charts': _CHARTS, 'data_table': None}\n"
        "if 'result_data' in globals():\n"
        "    _result['data_table'] = globals()['result_data']\n"
        "with open(os.path.join(OUT, '_meta.json'), 'w', encoding='utf-8') as _f:\n"
        "    json.dump(_result, _f, ensure_ascii=False, default=str)\n"
    )
    return wrapper
