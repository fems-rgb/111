# -*- coding: utf-8 -*-
import sys, io, os, json, warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
matplotlib.use('Agg')
warnings.filterwarnings('ignore', category=UserWarning)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

OUT = r'D:\111-1\AI_Scientist_v2\backend\output\experiments\4'
CDIR = r'D:\111-1\AI_Scientist_v2\backend\output\experiments\4\charts'
_CHARTS = []

_DF_JSON = '{"columns": ["x", "y"], "rows": [[1, 10], [2, 20], [3, 30]]}'

# === 图表捕获 ===
_orig_savefig = plt.savefig
def _save(*a, **kw):
    if a:
        p = a[0]
        if not os.path.isabs(str(p)):
            p = os.path.join(CDIR, str(p))
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
    for _f in sorted(_glb.glob(_os.path.join(CDIR, '*.png'))):
        if _f not in _st:
            _CHARTS.append(_f)
            _st.add(_f)
    plt.close('all')
plt.show = _show

# === Animation auto-save ===
import atexit
_ANIMS = []
_orig_FA = getattr(animation, 'FuncAnimation', None)
if _orig_FA is not None:
    class _TA(_orig_FA):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            _ANIMS.append(self)
    animation.FuncAnimation = _TA

def __run(__code):
    import builtins
    try:
        _dt = None if _DF_JSON == '__NONE__' else json.loads(_DF_JSON)
    except Exception:
        _dt = None
    df = None
    if _dt is not None:
        try:
            if isinstance(_dt, dict) and 'rows' in _dt:
                df = pd.DataFrame(_dt['rows'], columns=_dt.get('columns'))
            else:
                df = pd.DataFrame(_dt)
        except Exception:
            df = None
    _ns = {'__builtins__': builtins, 'df': df,
           'pd': pd, 'np': np, 'plt': plt, 'os': os, 'json': json}
    exec(__code, _ns)
    if 'result_data' in _ns:
        globals()['result_data'] = _ns['result_data']

__USER_CODE = (
    r"""
import pandas as pd, matplotlib.pyplot as plt
df = pd.DataFrame({'x':[1,2,3],'y':[10,20,30]})
print('OK', df['y'].sum())

"""
)

__run(__USER_CODE)

_result = {'charts': _CHARTS, 'data_table': None}
if 'result_data' in globals():
    _result['data_table'] = globals()['result_data']
with open(os.path.join(OUT, '_meta.json'), 'w', encoding='utf-8') as _f:
    json.dump(_result, _f, ensure_ascii=False, default=str)
