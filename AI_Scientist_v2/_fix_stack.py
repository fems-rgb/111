# -*- coding: utf-8 -*-
"""清除模板技术栈表(L87-88)的硬编码领域词 -> 通用描述"""
TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
src = open(TPL, encoding="utf-8").read()

fixes = [
    # L87: 机器学习用途
    ("CMB 功率谱拟合与参数约束",
     "观测数据拟合与关键参数约束"),
    # L88: 深度学习用途
    ("大尺度结构/宇宙网建模、CMB 图像特征提取",
     "复杂系统结构建模、观测图像特征提取"),
]
for old, new in fixes:
    if old in src:
        src = src.replace(old, new, 1)
        print(f"[替换] {old} -> {new}")
    else:
        print(f"[跳过] 未匹配: {old}")

open(TPL, "w", encoding="utf-8").write(src)
print("[完成]")
