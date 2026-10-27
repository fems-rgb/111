<template>
  <!-- 单个图解块：按 kind 渲染成真正的图形（流程 / 对比 / 要点卡 / 提示框） -->
  <div class="fig" :class="`fig-${block.kind}`">
    <!-- 流程 -->
    <div v-if="block.kind === 'flow'" class="fig-card">
      <p v-if="block.title" class="fig-title">{{ block.title }}</p>
      <div class="flow">
        <template v-for="(s, i) in block.steps" :key="i">
          <div class="flow-step">
            <span class="flow-no">{{ i + 1 }}</span>
            <div class="flow-body">
              <p class="flow-label">{{ s.label }}</p>
              <p v-if="s.desc" class="flow-desc">{{ s.desc }}</p>
            </div>
          </div>
          <span v-if="i < block.steps.length - 1" class="flow-arrow">→</span>
        </template>
      </div>
    </div>

    <!-- 对比 -->
    <div v-else-if="block.kind === 'compare'" class="fig-card">
      <p v-if="block.title" class="fig-title">{{ block.title }}</p>
      <div class="cmp">
        <div class="cmp-side cmp-left">
          <p class="cmp-head">{{ block.left.title }}</p>
          <ul>
            <li v-for="(it, i) in block.left.items" :key="i">{{ it }}</li>
          </ul>
        </div>
        <div class="cmp-vs">对比</div>
        <div class="cmp-side cmp-right">
          <p class="cmp-head">{{ block.right.title }}</p>
          <ul>
            <li v-for="(it, i) in block.right.items" :key="i">{{ it }}</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 要点卡 -->
    <div v-else-if="block.kind === 'cards'" class="fig-card">
      <p v-if="block.title" class="fig-title">{{ block.title }}</p>
      <div class="cards">
        <div v-for="(c, i) in block.cards" :key="i" class="card-item">
          <span class="card-icon">{{ c.icon || '•' }}</span>
          <div class="card-body">
            <p class="card-title">{{ c.title }}</p>
            <p v-if="c.desc" class="card-desc">{{ c.desc }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 提示框 -->
    <div v-else-if="block.kind === 'callout'" class="callout" :class="`tone-${block.tone}`">
      <span class="callout-icon">{{ toneIcon }}</span>
      <div>
        <p v-if="block.title" class="callout-title">{{ block.title }}</p>
        <p class="callout-text">{{ block.text }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FigureBlock } from '@/api/modules/general'

const props = defineProps<{ block: FigureBlock }>()

const toneIcon = computed(() => {
  if (props.block.kind !== 'callout') return ''
  return ({ tip: '💡', aha: '🔑', warn: '⚠️' } as const)[props.block.tone] || '💡'
})
</script>

<style scoped>
.fig { margin: 4px 0 20px; }
.fig-card {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 16px 18px;
  background: #fbfcfe;
}
.fig-title {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .04em;
  color: #2563eb;
  margin-bottom: 14px;
}

/* flow */
.flow { display: flex; flex-wrap: wrap; align-items: stretch; gap: 6px; }
.flow-step {
  flex: 1 1 120px;
  display: flex; gap: 10px; align-items: flex-start;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px;
}
.flow-no {
  flex-shrink: 0; width: 22px; height: 22px; border-radius: 50%;
  background: #2563eb; color: #fff; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.flow-label { font-size: 13px; font-weight: 600; color: #0f172a; }
.flow-desc { font-size: 11.5px; color: #64748b; margin-top: 2px; line-height: 1.5; }
.flow-arrow { align-self: center; color: #93c5fd; font-weight: 700; }

/* compare */
.cmp { display: flex; align-items: stretch; gap: 8px; }
.cmp-side { flex: 1; border-radius: 10px; padding: 12px 14px; }
.cmp-left { background: #eef2ff; }
.cmp-right { background: #f0fdf4; }
.cmp-head { font-size: 13px; font-weight: 700; margin-bottom: 8px; }
.cmp-left .cmp-head { color: #3730a3; }
.cmp-right .cmp-head { color: #166534; }
.cmp-side ul { list-style: none; padding: 0; margin: 0; }
.cmp-side li { font-size: 12.5px; color: #334155; line-height: 1.7; padding-left: 14px; position: relative; }
.cmp-side li::before { content: '·'; position: absolute; left: 2px; font-weight: 700; }
.cmp-vs { align-self: center; font-size: 11px; color: #94a3b8; flex-shrink: 0; }

/* cards */
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.card-item {
  display: flex; gap: 10px; align-items: flex-start;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px;
}
.card-icon { font-size: 20px; line-height: 1; flex-shrink: 0; }
.card-title { font-size: 13px; font-weight: 600; color: #0f172a; }
.card-desc { font-size: 11.5px; color: #64748b; margin-top: 3px; line-height: 1.5; }

/* callout */
.callout { display: flex; gap: 12px; border-radius: 12px; padding: 14px 16px; }
.callout-icon { font-size: 18px; line-height: 1.4; flex-shrink: 0; }
.callout-title { font-size: 13px; font-weight: 700; margin-bottom: 3px; }
.callout-text { font-size: 13px; line-height: 1.7; }
.tone-tip { background: #eff6ff; }
.tone-tip .callout-title, .tone-tip .callout-text { color: #1d4ed8; }
.tone-aha { background: #f5f3ff; }
.tone-aha .callout-title, .tone-aha .callout-text { color: #6d28d9; }
.tone-warn { background: #fffbeb; }
.tone-warn .callout-title, .tone-warn .callout-text { color: #92400e; }
</style>
