import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DengXian', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

import matplotlib.animation as animation
import numpy as np
import os, json, warnings
warnings.filterwarnings('ignore', category=UserWarning)

_CHARTS = []
_OUT = r'D:\111-1\AI_Scientist_v2\backend\output\experiments\900001'
_CDIR = r'D:\111-1\AI_Scientist_v2\backend\output\experiments\900001\charts'

_orig_savefig = plt.savefig
def _save(*a, **kw):
    if a:
        p = a[0]
        if not os.path.isabs(str(p)):
            p = os.path.join(_CDIR, str(p))
        a = (p,) + a[1:]
    kw.setdefault('dpi', 150)
    kw.setdefault('bbox_inches', 'tight')
    _orig_savefig(*a, **kw)
    _CHARTS.append(str(a[0]) if a else '')
plt.savefig = _save

_orig_show = plt.show
def _show(*a, **kw):
    import glob as _glb, os as _os
    _st = set(_CHARTS)
    for _f in sorted(_glb.glob(_os.path.join(_CDIR, "*.png"))):
        if _f not in _st:
            _CHARTS.append(_f)
            _st.add(_f)
    plt.close('all')
plt.show = _show

exec("""

""")

_result = {'charts': _CHARTS, 'data_table': None}
if 'result_data' in dir():
    _result['data_table'] = result_data
with open(os.path.join(_OUT, '_meta.json'), 'w', encoding='utf-8') as _f:
    json.dump(_result, _f, ensure_ascii=False, default=str)
