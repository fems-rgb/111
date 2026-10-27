<template>
  <!-- 模式感知徽标：把「当前快速/专家会怎样」在生成入口就近说清楚 -->
  <div class="flex items-start gap-2 rounded-lg border px-3 py-2 text-xs"
       :class="isExpert
         ? 'border-accent-200 bg-accent-50/60 text-accent-700'
         : 'border-primary-200 bg-primary-50/60 text-primary-700'">
    <span class="text-base leading-none mt-0.5">{{ isExpert ? '🔬' : '⚡' }}</span>
    <div class="min-w-0">
      <span class="font-semibold">{{ isExpert ? '专家模式' : '快速模式' }}</span>
      <span class="mx-1 opacity-40">·</span>
      <span>{{ line }}</span>
      <span v-if="!isExpert" class="opacity-70"> —— 想更详尽、更多图表？<span class="font-medium">切到专家模式</span></span>
      <span v-else class="opacity-70"> —— 想要更快更省？<span class="font-medium">切回快速模式</span></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

/** scope 决定文案：不同功能各自说明模式带来的差别 */
const props = withDefaults(defineProps<{ scope?: 'courseware' | 'general' | 'outline' }>(), {
  scope: 'courseware',
})

const appStore = useAppStore()
const isExpert = computed(() => appStore.mode === 'expert')

const LINES: Record<string, { quick: string; expert: string }> = {
  courseware: {
    quick: 'qwen-plus 精简 · 约 4 章、每章 4 页 · 每页 60-90 字讲透',
    expert: 'qwen-max 详尽 · 约 8 章、每章 6 页 · 每页 120-200 字 + 案例',
  },
  general: {
    quick: 'qwen-plus · 约 4 节、每节 500-700 字 · 图解 1 个',
    expert: 'qwen-max · 约 8 节、每节 900-1200 字 · 图解 2 个、更多案例',
  },
  outline: {
    quick: '每章只留 3-4 个核心知识点，抓主干',
    expert: '每章展开 5-8 个知识点，原理 / 方法 / 案例都覆盖',
  },
}

const line = computed(() => {
  const m = LINES[props.scope] || LINES.courseware
  return isExpert.value ? m.expert : m.quick
})
</script>
