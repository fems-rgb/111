# -*- coding: utf-8 -*-
"""AI Scientist 实验模拟场一键修复脚本 v2"""
import os, shutil

# 脚本位于 backend/patch_all.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = SCRIPT_DIR          # backend/
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)  # AI_Scientist/

def backup(path):
    bak = path + '.bak'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        print(f'  OK backup: {os.path.basename(bak)}')
    else:
        print(f'  skip backup (exists)')

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  OK write: {os.path.basename(path)}')

# ═══════════════════════════════════════════
# PATCH 1: experiment_engine.py
# ═══════════════════════════════════════════
print('\n[1/3] experiment_engine.py')
p1 = os.path.join(BACKEND_DIR, 'app', 'services', 'experiment_engine.py')
assert os.path.exists(p1), f'NOT FOUND: {p1}'
backup(p1)

ENGINE_CODE = r'''# -*- coding: utf-8 -*-
import os, sys, time, json, asyncio, logging
from typing import Optional

logger = logging.getLogger(__name__)
OUTPUT_ROOT = os.path.join(os.getcwd(), 'output', 'experiments')

FORBIDDEN = ['os.system', 'subprocess.run', 'subprocess.call', 'subprocess.Popen',
             'shutil.rmtree', '__import__', 'eval(', 'exec(', 'socket', 'ctypes']
FORBIDDEN_IMPORTS = ['socket', 'ctypes', 'multiprocessing', 'subprocess', 'shutil']

CN_FONT_SETUP = (
    "import matplotlib\n"
    "matplotlib.use('Agg')\n"
    "import matplotlib.pyplot as plt\n"
    "plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DengXian', 'DejaVu Sans']\n"
    "plt.rcParams['axes.unicode_minus'] = False\n"
)


def _check_safety(code: str) -> Optional[str]:
    for f in FORBIDDEN:
        if f in code:
            return f'\u5b89\u5168\u62e6\u622a: \u7981\u6b62\u4f7f\u7528 {f}'
    for m in FORBIDDEN_IMPORTS:
        if f'import {m}' in code or f'from {m}' in code:
            return f'\u5b89\u5168\u62e6\u622a: \u7981\u6b62\u5bfc\u5165 {m}'
    return None


def _build_wrapper(code: str, out_dir: str, charts_dir: str, generate_video: bool) -> str:
    safe_code = code.replace(chr(92), chr(92)+chr(92)).replace(chr(34)*3, chr(34)+chr(39)+chr(34))

    anim_hook = ''
    if generate_video:
        anim_hook = (
            "\n"
            "# === Animation auto-save hook ===\n"
            "import atexit\n"
            "_ANIMATIONS = []\n"
            "_orig_FuncAnimation = animation.FuncAnimation\n"
            "class _TrackedFuncAnimation(_orig_FuncAnimation):\n"
            "    def __init__(self, *a, **kw):\n"
            "        super().__init__(*a, **kw)\n"
            "        _ANIMATIONS.append(self)\n"
            "    def save(self, *a, **kw):\n"
            "        if a:\n"
            "            p = str(a[0])\n"
            "            if not os.path.isabs(p):\n"
            "                p = os.path.join(_OUT, p)\n"
            "            a = (p,) + a[1:]\n"
            "        super().save(*a, **kw)\n"
            "animation.FuncAnimation = _TrackedFuncAnimation\n"
            "\n"
            "def _auto_save_animations():\n"
            "    for ani in _ANIMATIONS:\n"
            "        try:\n"
            "            gif_path = os.path.join(_OUT, 'animation.gif')\n"
            "            mp4_path = os.path.join(_OUT, 'animation.mp4')\n"
            "            saved = False\n"
            "            try:\n"
            "                from matplotlib.animation import FFMpegWriter\n"
            "                writer = FFMpegWriter(fps=15, bitrate=1800)\n"
            "                ani.save(mp4_path, writer=writer)\n"
            "                saved = True\n"
            "            except Exception:\n"
            "                pass\n"
            "            if not saved:\n"
            "                try:\n"
            "                    from matplotlib.animation import PillowWriter\n"
            "                    writer = PillowWriter(fps=15)\n"
            "                    ani.save(gif_path, writer=writer)\n"
            "                    saved = True\n"
            "                except Exception:\n"
            "                    pass\n"
            "            if not saved:\n"
            "                try:\n"
            "                    ani.save(gif_path, writer='imagemagick')\n"
            "                except Exception:\n"
            "                    pass\n"
            "        except Exception:\n"
            "            pass\n"
            "atexit.register(_auto_save_animations)\n"
        )

    wrapper = (
        "import sys, io\n"
        "sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')\n"
        "sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')\n"
        "\n"
        + CN_FONT_SETUP +
        "\n"
        "import matplotlib.animation as animation\n"
        "import numpy as np\n"
        "import os, json, warnings\n"
        "warnings.filterwarnings('ignore', category=UserWarning)\n"
        "\n"
        "_CHARTS = []\n"
        f"_OUT = r'{out_dir}'\n"
        f"_CDIR = r'{charts_dir}'\n"
        "\n"
        "_orig_savefig = plt.savefig\n"
        "def _save(*a, **kw):\n"
        "    if a:\n"
        "        p = a[0]\n"
        "        if not os.path.isabs(str(p)):\n"
        "            p = os.path.join(_CDIR, str(p))\n"
        "        a = (p,) + a[1:]\n"
        "    kw.setdefault('dpi', 150)\n"
        "    kw.setdefault('bbox_inches', 'tight')\n"
        "    _orig_savefig(*a, **kw)\n"
        "    _CHARTS.append(str(a[0]) if a else '')\n"
        "plt.savefig = _save\n"
        "\n"
        "_orig_show = plt.show\n"
        "def _show(*a, **kw):\n"
        "    fn = os.path.join(_CDIR, f'figure_{len(_CHARTS)+1}.png')\n"
        "    plt.savefig(fn, dpi=150, bbox_inches='tight')\n"
        "    _CHARTS.append(fn)\n"
        "plt.show = _show\n"
        + anim_hook +
        "\n"
        "exec(\"\"\"\n"
        + safe_code +
        "\n\"\"\")\n"
        "\n"
        "_result = {'charts': _CHARTS, 'data_table': None}\n"
        "if 'result_data' in dir():\n"
        "    _result['data_table'] = result_data\n"
        "with open(os.path.join(_OUT, '_meta.json'), 'w', encoding='utf-8') as _f:\n"
        "    json.dump(_result, _f, ensure_ascii=False, default=str)\n"
    )
    return wrapper


async def run_experiment(code: str, run_id: int, timeout: int = 60,
                         generate_video: bool = True) -> dict:
    start = time.time()
    err = _check_safety(code)
    if err:
        return {'success': False, 'error': err, 'output_text': '',
                'charts': [], 'video_path': None, 'data_table': None, 'duration_ms': 0}

    out_dir = os.path.join(OUTPUT_ROOT, str(run_id))
    charts_dir = os.path.join(out_dir, 'charts')
    os.makedirs(charts_dir, exist_ok=True)

    wrapper = _build_wrapper(code, out_dir, charts_dir, generate_video)

    tmp = os.path.join(out_dir, '_run.py')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(wrapper)

    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['MPLBACKEND'] = 'Agg'
        proc = await asyncio.create_subprocess_exec(
            sys.executable, '-X', 'utf8', tmp,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            cwd=out_dir, env=env)
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        dur = int((time.time() - start) * 1000)
        sout = stdout.decode('utf-8', errors='replace')[:10000]
        serr = stderr.decode('utf-8', errors='replace')[:5000]

        serr_lines = [l for l in serr.split('\n')
                      if l.strip() and 'UserWarning' not in l and 'Glyph' not in l
                      and 'missing from font' not in l and '_orig_savefig' not in l
                      and '_auto_save' not in l and 'PillowWriter' not in l
                      and 'FFMpegWriter' not in l]
        serr_clean = '\n'.join(serr_lines).strip()

        if proc.returncode != 0:
            return {'success': False, 'output_text': sout, 'error': serr_clean[-2000:] or serr[-2000:],
                    'charts': [], 'video_path': None, 'data_table': None, 'duration_ms': dur}

        meta_path = os.path.join(out_dir, '_meta.json')
        charts_list = []
        data_table = None
        if os.path.exists(meta_path):
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
            charts_list = meta.get('charts', [])
            data_table = meta.get('data_table')

        if not charts_list:
            for fn in sorted(os.listdir(charts_dir)):
                if fn.endswith(('.png', '.jpg', '.svg')):
                    charts_list.append(os.path.join(charts_dir, fn))

        video_path = None
        if generate_video:
            mp4_path = os.path.join(out_dir, 'animation.mp4')
            gif_path = os.path.join(out_dir, 'animation.gif')
            if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 0:
                video_path = mp4_path
            elif os.path.exists(gif_path) and os.path.getsize(gif_path) > 0:
                video_path = gif_path
            else:
                for fn in os.listdir(out_dir):
                    if fn.endswith(('.mp4', '.gif', '.avi', '.mov')) and fn != '_run.py':
                        candidate = os.path.join(out_dir, fn)
                        if os.path.getsize(candidate) > 0:
                            video_path = candidate
                            break

        return {'success': True, 'output_text': sout,
                'charts': [{'path': c, 'filename': os.path.basename(c)} for c in charts_list if os.path.exists(c)],
                'video_path': video_path, 'data_table': data_table,
                'error': serr_clean if serr_clean else None, 'duration_ms': dur}
    except asyncio.TimeoutError:
        try: proc.kill()
        except: pass
        return {'success': False, 'output_text': '', 'error': f'\u6267\u884c\u8d85\u65f6({timeout}\u79d2)',
                'charts': [], 'video_path': None, 'data_table': None,
                'duration_ms': int((time.time()-start)*1000)}
    except Exception as e:
        return {'success': False, 'output_text': '', 'error': str(e)[:1000],
                'charts': [], 'video_path': None, 'data_table': None,
                'duration_ms': int((time.time()-start)*1000)}


BUILTIN_TEMPLATES = [
    {
        'name': '\u7ebf\u6027\u56de\u5f52\u6a21\u62df',
        'description': '\u751f\u6210\u5408\u6210\u6570\u636e\u5e76\u62df\u5408\u7ebf\u6027\u6a21\u578b\uff0c\u8f93\u51fa\u56de\u5f52\u7cfb\u6570\u3001R\u00b2\u503c\u548c\u6b8b\u5dee\u56fe',
        'category': '\u7edf\u8ba1\u5206\u6790',
        'code': (
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "from scipy import stats\n"
            "\n"
            "np.random.seed(42)\n"
            "n = 200\n"
            "X = np.random.uniform(0, 10, n)\n"
            "Y = 2.5 * X + 3 + np.random.normal(0, 1.5, n)\n"
            "\n"
            "slope, intercept, r_value, p_value, std_err = stats.linregress(X, Y)\n"
            "\n"
            "fig, axes = plt.subplots(1, 2, figsize=(12, 5))\n"
            "axes[0].scatter(X, Y, alpha=0.6, color='steelblue')\n"
            "axes[0].plot(X, intercept + slope * X, 'r-', linewidth=2,\n"
            "             label=f'y={slope:.2f}x+{intercept:.2f}')\n"
            "axes[0].set_title(f'R\u00b2={r_value**2:.4f}, p={p_value:.2e}')\n"
            "axes[0].set_xlabel('\u81ea\u53d8\u91cf X')\n"
            "axes[0].set_ylabel('\u56e0\u53d8\u91cf Y')\n"
            "axes[0].legend()\n"
            "\n"
            "residuals = Y - (slope * X + intercept)\n"
            "axes[1].scatter(slope*X+intercept, residuals, alpha=0.6, color='coral')\n"
            "axes[1].axhline(y=0, color='k', linestyle='--')\n"
            "axes[1].set_title('\u6b8b\u5dee\u5206\u5e03\u56fe')\n"
            "axes[1].set_xlabel('\u9884\u6d4b\u503c')\n"
            "axes[1].set_ylabel('\u6b8b\u5dee')\n"
            "plt.tight_layout()\n"
            "plt.savefig('regression.png', dpi=150, bbox_inches='tight')\n"
            "plt.show()\n"
            "\n"
            "result_data = {\n"
            "    'columns': ['\u6307\u6807', '\u6570\u503c'],\n"
            "    'rows': [['\u659c\u7387', f'{slope:.4f}'], ['\u622a\u8ddd', f'{intercept:.4f}'],\n"
            "             ['R\u00b2', f'{r_value**2:.4f}'], ['p\u503c', f'{p_value:.2e}']]\n"
            "}\n"
            "print(f'\u56de\u5f52\u5b8c\u6210: y={slope:.3f}x+{intercept:.3f}, R\u00b2={r_value**2:.4f}')\n"
        )
    },
    {
        'name': '\u8499\u7279\u5361\u6d1b\u4f30\u7b97\u5706\u5468\u7387',
        'description': '\u901a\u8fc7\u968f\u673a\u91c7\u6837\u4f30\u7b97pi\u503c\uff0c\u5c55\u793a\u6536\u655b\u8fc7\u7a0b',
        'category': '\u6570\u503c\u8ba1\u7b97',
        'code': (
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "\n"
            "np.random.seed(42)\n"
            "N = 5000\n"
            "x = np.random.uniform(-1, 1, N)\n"
            "y = np.random.uniform(-1, 1, N)\n"
            "inside = x**2 + y**2 <= 1\n"
            "pi_est = 4 * inside.sum() / N\n"
            "\n"
            "fig, ax = plt.subplots(figsize=(6, 6))\n"
            "ax.scatter(x[inside], y[inside], s=1, c='green', alpha=0.5, label='\u5706\u5185')\n"
            "ax.scatter(x[~inside], y[~inside], s=1, c='red', alpha=0.3, label='\u5706\u5916')\n"
            "circle = plt.Circle((0,0), 1, fill=False, color='k', lw=2)\n"
            "ax.add_patch(circle)\n"
            "ax.set_aspect('equal')\n"
            "ax.set_title(f'\u8499\u7279\u5361\u6d1b\u6cd5 \u03c0 = {pi_est:.4f}')\n"
            "ax.legend()\n"
            "plt.savefig('monte_carlo.png', dpi=150, bbox_inches='tight')\n"
            "plt.show()\n"
            "\n"
            "running = 4 * np.cumsum(inside) / np.arange(1, N+1)\n"
            "fig2, ax2 = plt.subplots(figsize=(8, 4))\n"
            "ax2.plot(running, 'b-', lw=0.5)\n"
            "ax2.axhline(y=np.pi, color='r', ls='--', label=f'\u771f\u5b9e\u03c0={np.pi:.6f}')\n"
            "ax2.set_xlabel('\u91c7\u6837\u6b21\u6570')\n"
            "ax2.set_ylabel('\u03c0 \u4f30\u8ba1\u503c')\n"
            "ax2.set_title('\u6536\u655b\u8fc7\u7a0b')\n"
            "ax2.legend()\n"
            "plt.savefig('convergence.png', dpi=150, bbox_inches='tight')\n"
            "plt.show()\n"
            "\n"
            "result_data = {\n"
            "    'columns': ['\u6307\u6807', '\u6570\u503c'],\n"
            "    'rows': [['\u91c7\u6837\u6570', str(N)], ['\u03c0\u4f30\u8ba1\u503c', f'{pi_est:.6f}'],\n"
            "             ['\u771f\u5b9e\u03c0', f'{np.pi:.6f}'], ['\u8bef\u5dee', f'{abs(pi_est-np.pi):.6f}']]\n"
            "}\n"
            "print(f'\u8499\u7279\u5361\u6d1b: \u03c0 = {pi_est:.6f}')\n"
        )
    },
    {
        'name': '\u6b63\u6001\u5206\u5e03\u4e0e\u4e2d\u5fc3\u6781\u9650\u5b9a\u7406',
        'description': '\u6f14\u793a\u4e2d\u5fc3\u6781\u9650\u5b9a\u7406\uff1a\u975e\u6b63\u6001\u6837\u672c\u5747\u503c\u7684\u5206\u5e03\u8d8b\u8fd1\u6b63\u6001',
        'category': '\u7edf\u8ba1\u5206\u6790',
        'code': (
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "from scipy import stats\n"
            "\n"
            "np.random.seed(42)\n"
            "sample_sizes = [1, 5, 30, 100]\n"
            "n_experiments = 10000\n"
            "\n"
            "fig, axes = plt.subplots(2, 2, figsize=(12, 8))\n"
            "for ax, n in zip(axes.flat, sample_sizes):\n"
            "    means = [np.mean(np.random.exponential(1, n)) for _ in range(n_experiments)]\n"
            "    ax.hist(means, bins=50, density=True, alpha=0.7, color='steelblue', edgecolor='white')\n"
            "    mu, sigma = np.mean(means), np.std(means)\n"
            "    x_range = np.linspace(mu - 4*sigma, mu + 4*sigma, 200)\n"
            "    ax.plot(x_range, stats.norm.pdf(x_range, mu, sigma), 'r-', lw=2, label='\u6b63\u6001\u62df\u5408')\n"
            "    ax.set_title(f'\u6837\u672c\u91cf n={n}')\n"
            "    ax.set_xlabel('\u6837\u672c\u5747\u503c')\n"
            "    ax.set_ylabel('\u6982\u7387\u5bc6\u5ea6')\n"
            "    ax.legend(fontsize=8)\n"
            "plt.suptitle('\u4e2d\u5fc3\u6781\u9650\u5b9a\u7406\u6f14\u793a(\u6307\u6570\u5206\u5e03\u91c7\u6837)', fontsize=14, fontweight='bold')\n"
            "plt.tight_layout()\n"
            "plt.savefig('clt.png', dpi=150, bbox_inches='tight')\n"
            "plt.show()\n"
            "\n"
            "result_data = {\n"
            "    'columns': ['\u6837\u672c\u91cf', '\u5747\u503c', '\u6807\u51c6\u5dee', '\u504f\u5ea6'],\n"
            "    'rows': [[str(n),\n"
            "              f'{np.mean([np.mean(np.random.exponential(1,n)) for _ in range(1000)]):.4f}',\n"
            "              f'{np.std([np.mean(np.random.exponential(1,n)) for _ in range(1000)]):.4f}',\n"
            "              f'{stats.skew([np.mean(np.random.exponential(1,n)) for _ in range(1000)]):.4f}']\n"
            "             for n in sample_sizes]\n"
            "}\n"
            "print('\u4e2d\u5fc3\u6781\u9650\u5b9a\u7406\u6f14\u793a\u5b8c\u6210')\n"
        )
    },
    {
        'name': '\u52a8\u6001\u6b63\u5f26\u6ce2\u52a8\u753b',
        'description': '\u4f7f\u7528 FuncAnimation \u751f\u6210\u6b63\u5f26\u6ce2\u4f20\u64ad\u52a8\u753b\uff0c\u81ea\u52a8\u4fdd\u5b58\u4e3a MP4/GIF',
        'category': '\u52a8\u6001\u53ef\u89c6\u5316',
        'code': (
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "import matplotlib.animation as animation\n"
            "\n"
            "fig, ax = plt.subplots(figsize=(8, 4))\n"
            "x = np.linspace(0, 2*np.pi, 200)\n"
            "line, = ax.plot(x, np.sin(x), 'b-', lw=2)\n"
            "ax.set_xlim(0, 2*np.pi)\n"
            "ax.set_ylim(-1.5, 1.5)\n"
            "ax.set_title('\u6b63\u5f26\u6ce2\u4f20\u64ad\u52a8\u753b')\n"
            "ax.set_xlabel('x')\n"
            "ax.set_ylabel('sin(x + t)')\n"
            "\n"
            "def update(frame):\n"
            "    line.set_ydata(np.sin(x + frame * 0.1))\n"
            "    ax.set_title(f'\u6b63\u5f26\u6ce2\u4f20\u64ad t={frame*0.1:.1f}')\n"
            "    return line,\n"
            "\n"
            "ani = animation.FuncAnimation(fig, update, frames=60, interval=50, blit=True)\n"
            "# \u65e0\u9700\u624b\u52a8\u8c03\u7528 ani.save() \u2014 \u7cfb\u7edf\u4f1a\u81ea\u52a8\u4fdd\u5b58\n"
            "plt.show()\n"
            "\n"
            "print('\u52a8\u753b\u751f\u6210\u5b8c\u6210\uff0c\u5171 60 \u5e27')\n"
        )
    },
]
'''

write_file(p1, ENGINE_CODE)


# ═══════════════════════════════════════════
# PATCH 2: experiment_lab.py
# ═══════════════════════════════════════════
print('\n[2/3] experiment_lab.py')
p2 = os.path.join(BACKEND_DIR, 'app', 'api', 'v1', 'experiment_lab.py')
assert os.path.exists(p2), f'NOT FOUND: {p2}'
backup(p2)

LAB_CODE = r'''# -*- coding: utf-8 -*-
"""实验模拟场 API - 动态模板 + 沙箱执行"""
import logging, os, mimetypes
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.database.session import get_db
from app.database.models import User, ExperimentRun, Project, ExperimentTemplate
from app.api.deps import get_current_user
from app.services.experiment_engine import run_experiment, BUILTIN_TEMPLATES

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/experiment-lab', tags=['实验模拟场'])


async def seed_builtin_templates(db: AsyncSession):
    """启动时自动写入内置模板（幂等）"""
    existing = (await db.execute(select(func.count()).select_from(ExperimentTemplate).where(
        ExperimentTemplate.is_builtin == True))).scalar() or 0
    if existing >= len(BUILTIN_TEMPLATES):
        return
    from sqlalchemy import delete
    await db.execute(delete(ExperimentTemplate).where(ExperimentTemplate.is_builtin == True))
    for t in BUILTIN_TEMPLATES:
        db.add(ExperimentTemplate(
            name=t['name'], description=t['description'],
            code=t['code'], category=t.get('category', '通用'),
            is_builtin=True))
    await db.commit()
    logger.info(f'已写入 {len(BUILTIN_TEMPLATES)} 个内置实验模板')


class RunRequest(BaseModel):
    code: str = Field(..., min_length=10, max_length=50000)
    title: str = Field('', max_length=200)
    project_id: Optional[int] = None
    question_task_id: Optional[int] = None
    generate_video: bool = True
    timeout: int = Field(60, ge=10, le=300)


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field('', max_length=1000)
    code: str = Field(..., min_length=10, max_length=50000)
    category: str = Field('自定义', max_length=100)


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    code: Optional[str] = Field(None, min_length=10, max_length=50000)
    category: Optional[str] = Field(None, max_length=100)


@router.post('/run')
async def run_exp(req: RunRequest, bg: BackgroundTasks,
                  db: AsyncSession = Depends(get_db),
                  user: User = Depends(get_current_user)):
    run = ExperimentRun(user_id=user.id, project_id=req.project_id,
                        question_task_id=req.question_task_id,
                        title=req.title or '未命名实验', code=req.code, status='running')
    db.add(run)
    await db.commit()
    await db.refresh(run)
    bg.add_task(_exec, run.id, req.code, req.timeout, req.generate_video)
    return {'run_id': run.id, 'status': 'running'}


async def _exec(run_id, code, timeout, gen_video):
    from app.database.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            run = (await db.execute(select(ExperimentRun).where(ExperimentRun.id == run_id))).scalar_one_or_none()
            if not run: return
            res = await run_experiment(code, run_id, timeout, gen_video)
            run.status = 'completed' if res['success'] else 'failed'
            run.output_text = res.get('output_text', '')
            run.charts = res.get('charts', [])
            run.video_path = res.get('video_path')
            run.data_table = res.get('data_table')
            run.error_message = res.get('error', '') or ''
            run.duration_ms = res.get('duration_ms', 0)
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()
            if run.project_id and res['charts']:
                proj = (await db.execute(select(Project).where(Project.id == run.project_id))).scalar_one_or_none()
                if proj:
                    ev = list(proj.evidence_files or [])
                    for c in res['charts']:
                        if c.get('path') and c['path'] not in ev: ev.append(c['path'])
                    if res.get('video_path'): ev.append(res['video_path'])
                    proj.evidence_files = ev
                    await db.commit()
        except Exception as e:
            logger.error(f'实验执行异常: {e}', exc_info=True)


@router.get('/status/{run_id}')
async def status(run_id: int, db: AsyncSession = Depends(get_db),
                 user: User = Depends(get_current_user)):
    run = (await db.execute(select(ExperimentRun).where(
        ExperimentRun.id == run_id, ExperimentRun.user_id == user.id))).scalar_one_or_none()
    if not run: raise HTTPException(404, '实验记录不存在')
    return {'run_id': run.id, 'status': run.status, 'title': run.title,
            'output_text': run.output_text, 'charts': run.charts or [],
            'video_path': run.video_path, 'data_table': run.data_table,
            'error_message': run.error_message, 'duration_ms': run.duration_ms,
            'created_at': run.created_at.isoformat() if run.created_at else None,
            'completed_at': run.completed_at.isoformat() if run.completed_at else None}


@router.get('/history')
async def history(page: int = 1, page_size: int = 20, project_id: Optional[int] = None,
                  db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    base = select(ExperimentRun).where(ExperimentRun.user_id == user.id)
    if project_id: base = base.where(ExperimentRun.project_id == project_id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
    rows = (await db.execute(base.order_by(ExperimentRun.created_at.desc())
                             .offset((page-1)*page_size).limit(page_size))).scalars().all()
    return {'total': total, 'items': [{'run_id': r.id, 'title': r.title, 'status': r.status,
            'charts_count': len(r.charts or []), 'has_video': bool(r.video_path),
            'duration_ms': r.duration_ms,
            'created_at': r.created_at.isoformat() if r.created_at else None} for r in rows]}


@router.get('/templates')
async def list_templates(db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)):
    await seed_builtin_templates(db)
    rows = (await db.execute(
        select(ExperimentTemplate).order_by(ExperimentTemplate.is_builtin.desc(), ExperimentTemplate.id)
    )).scalars().all()
    return {'templates': [{'id': r.id, 'name': r.name, 'description': r.description,
                           'category': r.category, 'is_builtin': r.is_builtin} for r in rows]}


@router.get('/templates/{tid}')
async def get_template(tid: int, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    t = (await db.execute(select(ExperimentTemplate).where(ExperimentTemplate.id == tid))).scalar_one_or_none()
    if not t: raise HTTPException(404, '模板不存在')
    return {'id': t.id, 'name': t.name, 'description': t.description,
            'code': t.code, 'category': t.category, 'is_builtin': t.is_builtin}


@router.post('/templates')
async def create_template(req: TemplateCreate, db: AsyncSession = Depends(get_db),
                          user: User = Depends(get_current_user)):
    t = ExperimentTemplate(name=req.name, description=req.description,
                           code=req.code, category=req.category,
                           is_builtin=False, user_id=user.id)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {'id': t.id, 'name': t.name, 'message': '模板创建成功'}


@router.put('/templates/{tid}')
async def update_template(tid: int, req: TemplateUpdate, db: AsyncSession = Depends(get_db),
                          user: User = Depends(get_current_user)):
    t = (await db.execute(select(ExperimentTemplate).where(ExperimentTemplate.id == tid))).scalar_one_or_none()
    if not t: raise HTTPException(404, '模板不存在')
    if t.is_builtin: raise HTTPException(403, '内置模板不可修改')
    if req.name is not None: t.name = req.name
    if req.description is not None: t.description = req.description
    if req.code is not None: t.code = req.code
    if req.category is not None: t.category = req.category
    await db.commit()
    return {'id': t.id, 'message': '模板更新成功'}


@router.delete('/templates/{tid}')
async def delete_template(tid: int, db: AsyncSession = Depends(get_db),
                          user: User = Depends(get_current_user)):
    t = (await db.execute(select(ExperimentTemplate).where(ExperimentTemplate.id == tid))).scalar_one_or_none()
    if not t: raise HTTPException(404, '模板不存在')
    if t.is_builtin: raise HTTPException(403, '内置模板不可删除')
    await db.delete(t)
    await db.commit()
    return {'message': '模板已删除'}


@router.get('/chart/{run_id}/{filename}')
async def chart_file(run_id: int, filename: str,
                     db: AsyncSession = Depends(get_db),
                     user: User = Depends(get_current_user)):
    from app.services.experiment_engine import OUTPUT_ROOT
    safe_name = os.path.basename(filename)
    p = os.path.join(OUTPUT_ROOT, str(run_id), 'charts', safe_name)
    real_p = os.path.realpath(p)
    real_root = os.path.realpath(os.path.join(OUTPUT_ROOT, str(run_id), 'charts'))
    if not real_p.startswith(real_root) or not os.path.exists(real_p):
        raise HTTPException(404, '图表文件不存在')
    media, _ = mimetypes.guess_type(real_p)
    if not media:
        media = 'image/png'
    return FileResponse(real_p, media_type=media, headers={'Cache-Control': 'public, max-age=3600'})


@router.get('/video/{run_id}')
async def video_file(run_id: int, db: AsyncSession = Depends(get_db),
                     user: User = Depends(get_current_user)):
    run = (await db.execute(select(ExperimentRun).where(
        ExperimentRun.id == run_id, ExperimentRun.user_id == user.id))).scalar_one_or_none()
    if not run or not run.video_path or not os.path.exists(run.video_path):
        raise HTTPException(404, '视频文件不存在')
    media, _ = mimetypes.guess_type(run.video_path)
    if not media:
        ext = os.path.splitext(run.video_path)[1].lower()
        media_map = {'.mp4': 'video/mp4', '.gif': 'image/gif', '.avi': 'video/x-msvideo',
                     '.mov': 'video/quicktime', '.webm': 'video/webm'}
        media = media_map.get(ext, 'application/octet-stream')
    return FileResponse(run.video_path, media_type=media, headers={'Cache-Control': 'public, max-age=3600'})
'''

write_file(p2, LAB_CODE)


# ═══════════════════════════════════════════
# PATCH 3: Frontend files
# ═══════════════════════════════════════════
print('\n[3/3] Frontend files')

# 3a: experiment.ts
ts_path = os.path.join(PROJECT_DIR, 'frontend', 'src', 'api', 'modules', 'experiment.ts')
assert os.path.exists(ts_path), f'NOT FOUND: {ts_path}'
backup(ts_path)

TS_CODE = """import client from '../client'
import { useAuthStore } from '@/stores/auth'

export interface ExperimentStatus {
  run_id: number; status: string; title: string; output_text: string
  charts: Array<{path: string; filename: string}>; video_path: string | null
  data_table: {columns: string[]; rows: string[][]} | null
  error_message: string; duration_ms: number
  created_at?: string; completed_at?: string
}

export interface TemplateInfo {
  id: number; name: string; description: string; category: string; is_builtin: boolean
}

export function runExperiment(data: {code: string; title?: string; project_id?: number; question_task_id?: number; generate_video?: boolean; timeout?: number}) {
  return client.post<{run_id: number; status: string}>('/experiment-lab/run', data)
}
export function getExperimentStatus(id: number) {
  return client.get<ExperimentStatus>(`/experiment-lab/status/${id}`)
}
export function getExperimentHistory(params: {page?: number; page_size?: number; project_id?: number}) {
  return client.get<{total: number; items: any[]}>('/experiment-lab/history', {params})
}
export function getExperimentTemplates() {
  return client.get<{templates: TemplateInfo[]}>('/experiment-lab/templates')
}
export function getTemplateCode(id: number) {
  return client.get<{id: number; name: string; code: string; description: string; category: string}>(`/experiment-lab/templates/${id}`)
}
export function createTemplate(data: {name: string; description: string; code: string; category?: string}) {
  return client.post<{id: number; name: string; message: string}>('/experiment-lab/templates', data)
}
export function updateTemplate(id: number, data: {name?: string; description?: string; code?: string; category?: string}) {
  return client.put<{id: number; message: string}>(`/experiment-lab/templates/${id}`, data)
}
export function deleteTemplate(id: number) {
  return client.delete<{message: string}>(`/experiment-lab/templates/${id}`)
}

/** Get chart URL - uses authenticated API endpoint */
export function getChartUrl(runId: number, filename: string) {
  return `/api/v1/experiment-lab/chart/${runId}/${filename}`
}

/** Get video URL - uses authenticated API endpoint */
export function getVideoUrl(runId: number) {
  return `/api/v1/experiment-lab/video/${runId}`
}

/** Detect if video path is a video format (mp4/avi/mov/webm) vs gif */
export function isVideoFormat(videoPath: string | null): boolean {
  if (!videoPath) return false
  const ext = videoPath.toLowerCase().split('.').pop() || ''
  return ['mp4', 'avi', 'mov', 'webm'].includes(ext)
}
"""

write_file(ts_path, TS_CODE)

# 3b: ExperimentLab.vue
vue_path = os.path.join(PROJECT_DIR, 'frontend', 'src', 'views', 'workspace', 'ExperimentLab.vue')
assert os.path.exists(vue_path), f'NOT FOUND: {vue_path}'
backup(vue_path)

VUE_CODE = '''<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">\ud83e\uddea \u5b9e\u9a8c\u6a21\u62df\u573a</h1>
        <p class="text-sm text-gray-500 mt-1">\u4ee3\u7801\u9a71\u52a8\u7684\u79d1\u5b66\u5b9e\u9a8c\u6a21\u62df \u00b7 \u56fe\u8868\u751f\u6210 \u00b7 \u52a8\u6001\u53ef\u89c6\u5316</p>
      </div>
      <div class="flex gap-2">
        <button @click="openNewTemplate" class="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm hover:bg-emerald-700">\u2795 \u65b0\u5efa\u6a21\u677f</button>
        <button @click="showTemplates=true" class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700">\ud83d\udcda \u6a21\u677f\u5e93</button>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <div class="space-y-4">
        <div class="bg-white rounded-xl border overflow-hidden">
          <div class="px-4 py-3 border-b flex items-center justify-between">
            <span class="text-sm font-medium">\ud83d\udcdd \u5b9e\u9a8c\u4ee3\u7801</span>
            <select v-model="selTplId" @change="onSelectTemplate" class="text-xs border rounded px-2 py-1">
              <option :value="null">\u9009\u62e9\u6a21\u677f...</option>
              <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
          </div>
          <textarea v-model="code" rows="18" spellcheck="false"
            class="w-full p-4 font-mono text-xs leading-relaxed resize-y focus:outline-none bg-gray-50"
            placeholder="# \u5728\u6b64\u7f16\u5199\u5b9e\u9a8c\u4ee3\u7801...&#10;# \u652f\u6301: numpy, matplotlib, scipy, pandas&#10;# plt.savefig() / plt.show() \u81ea\u52a8\u6355\u83b7\u56fe\u8868&#10;# \u5b9a\u4e49 result_data = {\'columns\':[], \'rows\':[]} \u8f93\u51fa\u6570\u636e\u8868&#10;# \u4f7f\u7528 FuncAnimation \u81ea\u52a8\u751f\u6210\u52a8\u753b(MP4/GIF)"></textarea>
        </div>
        <div class="flex items-center gap-4">
          <input v-model="expTitle" placeholder="\u5b9e\u9a8c\u540d\u79f0" class="flex-1 px-3 py-2 border rounded-lg text-sm"/>
          <label class="flex items-center gap-1 text-sm whitespace-nowrap">
            <input type="checkbox" v-model="genVideo"/> \u751f\u6210\u52a8\u753b
          </label>
          <button @click="submitRun" :disabled="running || !code.trim()"
            class="px-6 py-2 rounded-lg font-medium text-white transition-all whitespace-nowrap"
            :class="running||!code.trim()?\'bg-gray-300 cursor-not-allowed\':\'bg-emerald-600 hover:bg-emerald-700 shadow-lg\'">
            {{ running ? \'\u23f3 \u8fd0\u884c\u4e2d...\' : \'\u25b6\ufe0f \u8fd0\u884c\u5b9e\u9a8c\' }}
          </button>
        </div>
      </div>

      <div class="space-y-4">
        <div v-if="result" class="bg-white rounded-xl border p-4 space-y-3">
          <div class="flex items-center gap-3">
            <span class="w-3 h-3 rounded-full"
              :class="{\'bg-yellow-400 animate-pulse\': result.status===\'running\', \'bg-green-500\': result.status===\'completed\', \'bg-red-500\': result.status===\'failed\'}">
            </span>
            <span class="text-sm font-medium">{{ statusLabel(result.status) }}</span>
            <span v-if="result.duration_ms" class="text-xs text-gray-400 ml-auto">\u23f1 {{ (result.duration_ms/1000).toFixed(1) }}\u79d2</span>
          </div>

          <div v-if="result.error_message" class="bg-red-50 border border-red-200 rounded-lg p-3">
            <p class="text-xs font-medium text-red-600 mb-1">\u274c \u9519\u8bef\u4fe1\u606f</p>
            <pre class="text-xs text-red-700 whitespace-pre-wrap">{{ result.error_message }}</pre>
          </div>

          <div v-if="result.output_text" class="bg-gray-900 rounded-lg p-3">
            <p class="text-xs text-gray-400 mb-1">\ud83d\udda5 \u63a7\u5236\u53f0\u8f93\u51fa</p>
            <pre class="text-xs text-green-400 whitespace-pre-wrap max-h-40 overflow-y-auto">{{ result.output_text }}</pre>
          </div>

          <div v-if="result.data_table" class="overflow-x-auto border rounded-lg">
            <p class="text-xs text-gray-500 px-3 pt-2">\ud83d\udcca \u6570\u636e\u7ed3\u679c</p>
            <table class="w-full text-xs">
              <thead class="bg-gray-50"><tr>
                <th v-for="c in result.data_table.columns" :key="c" class="px-3 py-2 text-left border-b">{{ c }}</th>
              </tr></thead>
              <tbody><tr v-for="(row, i) in result.data_table.rows" :key="i" class="border-b last:border-0">
                <td v-for="(cell, j) in row" :key="j" class="px-3 py-1.5">{{ cell }}</td>
              </tr></tbody>
            </table>
          </div>

          <div v-if="result.charts && result.charts.length" class="space-y-3">
            <p class="text-xs text-gray-500">\ud83d\udcc8 \u751f\u6210\u56fe\u8868 ({{ result.charts.length }})</p>
            <img v-for="c in result.charts" :key="c.filename" :src="chartUrl(c)"
              class="w-full rounded-lg border" loading="lazy"/>
          </div>

          <div v-if="result.video_path">
            <p class="text-xs text-gray-500 mb-2">\ud83c\udfac \u52a8\u6001\u8fc7\u7a0b</p>
            <video v-if="isVideoFormat(result.video_path)"
              :src="videoUrl()" controls autoplay loop muted
              class="w-full rounded-lg border" preload="metadata">
              \u60a8\u7684\u6d4f\u89c8\u5668\u4e0d\u652f\u6301\u89c6\u9891\u64ad\u653e
            </video>
            <img v-else :src="videoUrl()" class="w-full rounded-lg border" loading="lazy"/>
          </div>
        </div>

        <div v-else class="bg-white rounded-xl border-dashed border-2 p-12 text-center">
          <p class="text-4xl mb-3">\ud83e\uddef</p>
          <p class="text-gray-500">\u7f16\u5199\u4ee3\u7801\u5e76\u70b9\u51fb\u300c\u8fd0\u884c\u5b9e\u9a8c\u300d\u67e5\u770b\u7ed3\u679c</p>
          <p class="text-xs text-gray-400 mt-2">\u652f\u6301 numpy \u00b7 matplotlib \u00b7 scipy \u00b7 pandas \u00b7 FuncAnimation</p>
        </div>
      </div>
    </div>

    <div v-if="showTemplates" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showTemplates=false">
      <div class="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl max-h-[80vh] overflow-y-auto">
        <h3 class="text-lg font-bold mb-4">\ud83d\udcda \u5b9e\u9a8c\u6a21\u677f\u5e93</h3>
        <div v-if="templates.length === 0" class="text-center text-gray-400 py-8">\u6682\u65e0\u6a21\u677f\uff0c\u70b9\u51fb\u300c\u65b0\u5efa\u6a21\u677f\u300d\u521b\u5efa</div>
        <div class="space-y-3">
          <div v-for="t in templates" :key="t.id"
            class="p-4 border rounded-xl hover:border-blue-400 hover:bg-blue-50 transition-all group">
            <div class="flex items-start justify-between">
              <div class="flex-1 cursor-pointer" @click="applyTemplate(t.id)">
                <div class="flex items-center gap-2">
                  <p class="font-medium text-sm">{{ t.name }}</p>
                  <span v-if="t.is_builtin" class="text-[10px] px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded">\u5185\u7f6e</span>
                  <span class="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">{{ t.category }}</span>
                </div>
                <p class="text-xs text-gray-500 mt-1">{{ t.description }}</p>
              </div>
              <button v-if="!t.is_builtin" @click.stop="removeTemplate(t.id)"
                class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 text-xs ml-2 transition-opacity">\u5220\u9664</button>
            </div>
          </div>
        </div>
        <button @click="showTemplates=false" class="mt-4 w-full py-2 text-sm text-gray-500 hover:text-gray-700">\u5173\u95ed</button>
      </div>
    </div>

    <div v-if="showNewTpl" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showNewTpl=false">
      <div class="bg-white rounded-2xl p-6 w-full max-w-2xl shadow-2xl">
        <h3 class="text-lg font-bold mb-4">\u2795 \u65b0\u5efa\u5b9e\u9a8c\u6a21\u677f</h3>
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <input v-model="newTpl.name" placeholder="\u6a21\u677f\u540d\u79f0" class="px-3 py-2 border rounded-lg text-sm"/>
            <input v-model="newTpl.category" placeholder="\u5206\u7c7b\uff08\u5982\uff1a\u7edf\u8ba1\u5206\u6790\uff09" class="px-3 py-2 border rounded-lg text-sm"/>
          </div>
          <input v-model="newTpl.description" placeholder="\u6a21\u677f\u63cf\u8ff0" class="w-full px-3 py-2 border rounded-lg text-sm"/>
          <textarea v-model="newTpl.code" rows="12" spellcheck="false"
            class="w-full p-3 font-mono text-xs border rounded-lg bg-gray-50 resize-y"
            placeholder="# \u5728\u6b64\u7f16\u5199\u6a21\u677f\u4ee3\u7801..."></textarea>
        </div>
        <div class="flex gap-3 mt-4">
          <button @click="saveNewTemplate" :disabled="!newTpl.name||!newTpl.code.trim()"
            class="flex-1 py-2 rounded-lg text-white text-sm font-medium"
            :class="!newTpl.name||!newTpl.code.trim()?\'bg-gray-300\':\'bg-emerald-600 hover:bg-emerald-700\'">\u4fdd\u5b58\u6a21\u677f</button>
          <button @click="showNewTpl=false" class="px-6 py-2 rounded-lg border text-sm text-gray-500 hover:bg-gray-50">\u53d6\u6d88</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from \'vue\'
import {
  runExperiment, getExperimentStatus, getExperimentTemplates,
  getTemplateCode, createTemplate, deleteTemplate,
  getChartUrl, getVideoUrl, isVideoFormat,
  type ExperimentStatus, type TemplateInfo
} from \'@/api/modules/experiment\'
import { useAppStore } from \'@/stores/app\'

const store = useAppStore()
const code = ref(\'\')
const expTitle = ref(\'\')
const genVideo = ref(true)
const running = ref(false)
const result = ref<ExperimentStatus | null>(null)
const templates = ref<TemplateInfo[]>([])
const selTplId = ref<number | null>(null)
const showTemplates = ref(false)
const showNewTpl = ref(false)
const newTpl = ref({ name: \'\', description: \'\', code: \'\', category: \'\u81ea\u5b9a\u4e49\' })
let timer: any = null

async function submitRun() {
  if (!code.value.trim() || running.value) return
  running.value = true
  result.value = null
  try {
    const r = await runExperiment({
      code: code.value,
      title: expTitle.value || \'\u672a\u547d\u540d\u5b9e\u9a8c\',
      generate_video: genVideo.value,
      timeout: 120
    })
    poll(r.data.run_id)
    store.showToast(\'\ud83e\uddea \u5b9e\u9a8c\u5df2\u63d0\u4ea4\u8fd0\u884c\', \'success\')
  } catch (e: any) {
    store.showToast(\'\u63d0\u4ea4\u5931\u8d25: \' + (e.response?.data?.detail || e.message), \'error\')
    running.value = false
  }
}

function poll(id: number) {
  if (timer) clearInterval(timer)
  timer = setInterval(async () => {
    try {
      const r = await getExperimentStatus(id)
      result.value = r.data
      if (r.data.status === \'completed\' || r.data.status === \'failed\') {
        clearInterval(timer); timer = null; running.value = false
        if (r.data.status === \'completed\') store.showToast(\'\u2705 \u5b9e\u9a8c\u5b8c\u6210\uff01\', \'success\')
        else store.showToast(\'\u274c \u5b9e\u9a8c\u5931\u8d25\', \'error\')
      }
    } catch { /* ignore polling errors */ }
  }, 2000)
}

function chartUrl(c: { filename: string }) {
  return result.value ? getChartUrl(result.value.run_id, c.filename) : \'\'
}
function videoUrl() {
  return result.value ? getVideoUrl(result.value.run_id) : \'\'
}
function statusLabel(s: string) {
  return ({ pending: \'\u7b49\u5f85\u4e2d\', running: \'\u8fd0\u884c\u4e2d\', completed: \'\u5df2\u5b8c\u6210\', failed: \'\u5931\u8d25\' } as any)[s] || s
}

async function loadTemplates() {
  try {
    const r = await getExperimentTemplates()
    templates.value = r.data.templates
  } catch { /* silent */ }
}

async function applyTemplate(id: number) {
  try {
    const r = await getTemplateCode(id)
    code.value = r.data.code
    expTitle.value = r.data.name
    selTplId.value = id
    showTemplates.value = false
    store.showToast(\'\ud83d\udccb \u5df2\u52a0\u8f7d\u6a21\u677f: \' + r.data.name, \'success\')
  } catch (e: any) {
    store.showToast(\'\u52a0\u8f7d\u6a21\u677f\u5931\u8d25\', \'error\')
  }
}

function onSelectTemplate() {
  if (selTplId.value) applyTemplate(selTplId.value)
}

function openNewTemplate() {
  if (code.value.trim()) {
    newTpl.value.code = code.value
    newTpl.value.name = expTitle.value || \'\'
  } else {
    newTpl.value = { name: \'\', description: \'\', code: \'\', category: \'\u81ea\u5b9a\u4e49\' }
  }
  showNewTpl.value = true
}

async function saveNewTemplate() {
  if (!newTpl.value.name || !newTpl.value.code.trim()) return
  try {
    await createTemplate(newTpl.value)
    store.showToast(\'\u2705 \u6a21\u677f\u5df2\u4fdd\u5b58\', \'success\')
    showNewTpl.value = false
    await loadTemplates()
  } catch (e: any) {
    store.showToast(\'\u4fdd\u5b58\u5931\u8d25: \' + (e.response?.data?.detail || e.message), \'error\')
  }
}

async function removeTemplate(id: number) {
  if (!confirm(\'\u786e\u5b9a\u5220\u9664\u6b64\u6a21\u677f\uff1f\')) return
  try {
    await deleteTemplate(id)
    store.showToast(\'\ud83d\uddd1\ufe0f \u6a21\u677f\u5df2\u5220\u9664\', \'success\')
    await loadTemplates()
  } catch (e: any) {
    store.showToast(\'\u5220\u9664\u5931\u8d25: \' + (e.response?.data?.detail || e.message), \'error\')
  }
}

onMounted(loadTemplates)
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>
'''

write_file(vue_path, VUE_CODE)

print('\n' + '='*50)
print('ALL 3 PATCHES APPLIED SUCCESSFULLY')
print('='*50)
print('\nNext steps:')
print('  1. Restart backend')
print('  2. cd frontend && npm run build')
print('  3. Refresh browser')