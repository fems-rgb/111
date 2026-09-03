<template>
  <span :class="badgeClass">{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const statusMap: Record<string, { label: string; class: string }> = {
  draft: { label: '草稿', class: 'badge bg-surface-100 text-surface-600' },
  planning: { label: '规划中', class: 'badge bg-blue-100 text-blue-800' },
  running: { label: '运行中', class: 'badge bg-green-100 text-green-800 animate-pulse' },
  waiting_review: { label: '待审核', class: 'badge bg-yellow-100 text-yellow-800' },
  completed: { label: '已完成', class: 'badge bg-green-100 text-green-800' },
  failed: { label: '失败', class: 'badge bg-red-100 text-red-800' },
  paused: { label: '已暂停', class: 'badge bg-orange-100 text-orange-800' },
  pending: { label: '等待中', class: 'badge bg-surface-100 text-surface-600' },
  skipped: { label: '已跳过', class: 'badge bg-surface-100 text-surface-400' },
  ok: { label: '成功', class: 'badge-success' },
  error: { label: '错误', class: 'badge-error' },
}

const badgeClass = computed(() => statusMap[props.status]?.class || 'badge bg-surface-100 text-surface-600')
const label = computed(() => statusMap[props.status]?.label || props.status)
</script>