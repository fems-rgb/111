# -*- coding: utf-8 -*-
"""精确读取两处关键代码：QuestionsView 的 result 消费 + KnowledgeView 的 fetchUrlsBatch"""
import os
files = {
    "knowledge.ts": r"D:\111-1\AI_Scientist_v2\frontend\src\api\modules\knowledge.ts",
    "QuestionsView.vue": r"D:\111-1\AI_Scientist_v2\frontend\src\views\workspace\QuestionsView.vue",
    "KnowledgeView.vue": r"D:\111-1\AI_Scientist_v2\frontend\src\views\knowledge\KnowledgeView.vue",
}
for name, fp in files.items():
    print("="*72)
    print(name, "✓" if os.path.exists(fp) else "❌ 不存在")
    print("="*72)
    if os.path.exists(fp):
        lines = open(fp, encoding="utf-8", errors="ignore").read().split("\n")
        # 只打印关键段
        for i, l in enumerate(lines):
            if name == "knowledge.ts" and i >= 75 and i <= 105:
                print(f"L{i+1:>3}| {l.rstrip()[:260]}")
            if name == "QuestionsView.vue" and 510 <= i <= 560:
                print(f"L{i+1:>3}| {l.rstrip()[:260]}")
            if name == "KnowledgeView.vue" and 390 <= i <= 470:
                print(f"L{i+1:>3}| {l.rstrip()[:260]}")
