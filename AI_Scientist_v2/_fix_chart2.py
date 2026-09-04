# -*- coding: utf-8 -*-
"""修复 export.py stageE：删硬编码错误路径，改成本项目动态目录"""
import shutil, re
P = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"
shutil.copy(P, P + ".bak_chart2")
src = open(P, encoding="utf-8").read()

# 用正则替换（不依赖精确转义，稳健）
pattern = re.compile(
    r"        _EXP=r'D:\\\\AI_Scientist\\\\AI_Scientist\\\\backend\\\\output\\\\experiments'\s*\n"
    r"        _all_png=\{_os\.path\.basename\(_p\):_p for _p in _glob\.glob\(_EXP\+r'\\\\\\\*\\\*\\\\\\\.png', recursive=True\)\}",
    re.M
)
NEW = '''        # [fix] 动态定位【本项目】真实图表目录（不再硬编码其他项目路径）
        _PROJ_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        _CANDIDATE_DIRS = [
            _os.path.join(_PROJ_ROOT, 'output', 'deliverables', f'project_{project_id}', 'charts'),
            _os.path.join(_PROJ_ROOT, 'output', 'deliverables', f'project_{project_id}'),
            _os.path.join(_PROJ_ROOT, 'output', 'experiments', f'project_{project_id}', 'charts'),
            _os.path.join(_PROJ_ROOT, 'output', 'experiments', str(project_id), 'charts'),
        ]
        _all_png = {}
        for _d in _CANDIDATE_DIRS:
            if _os.path.isdir(_d):
                for _f in sorted(_os.listdir(_d)):
                    if _f.lower().endswith(('.png','.jpg','.jpeg','.svg')):
                        _all_png[_f] = _os.path.join(_d, _f)
        if not _all_png:
            logger.warning('[stageE] project_%s 无专属图表，不填充占位图', project_id)'''

m = pattern.search(src)
if m:
    src = src[:m.start()] + NEW + src[m.end():]
    open(P, "w", encoding="utf-8").write(src)
    print("[已修改] 硬编码路径 → 本项目动态目录")
else:
    print("[正则未匹配] 改用行号精确替换（更稳）")
    lines = src.split("\n")
    # L628-629 整体替换为空（后面统一重建 _all_png）
    lines[627:629] = [
        "        # [fix] 动态定位本项目图表目录",
        "        _PROJ_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))",
        "        _CANDIDATE_DIRS = [",
        "            _os.path.join(_PROJ_ROOT, 'output', 'deliverables', f'project_{project_id}', 'charts'),",
        "            _os.path.join(_PROJ_ROOT, 'output', 'deliverables', f'project_{project_id}'),",
        "            _os.path.join(_PROJ_ROOT, 'output', 'experiments', f'project_{project_id}', 'charts'),",
        "            _os.path.join(_PROJ_ROOT, 'output', 'experiments', str(project_id), 'charts'),",
        "        ]",
        "        _all_png = {}",
        "        for _d in _CANDIDATE_DIRS:",
        "            if _os.path.isdir(_d):",
        "                for _f in sorted(_os.listdir(_d)):",
        "                    if _f.lower().endswith(('.png','.jpg','.jpeg','.svg')):",
        "                        _all_png[_f] = _os.path.join(_d, _f)",
        "        if not _all_png:",
        "            logger.warning('[stageE] project_%s 无专属图表，不填充占位图', project_id)",
    ]
    open(P, "w", encoding="utf-8").write("\n".join(lines))
    print("[已用行号替换] L628-629 → 动态目录逻辑")

# 验证
lines2 = open(P, encoding="utf-8").read().split("\n")
print("\n现在 L625-660：")
for i in range(624, 660):
    print(f"L{i+1:>3}| {lines2[i].rstrip()[:160]}")
