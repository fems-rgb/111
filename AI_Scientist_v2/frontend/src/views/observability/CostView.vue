<template>
  <div class="space-y-6 animate-fade-in">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="card text-center">
        <p class="text-3xl font-bold text-primary-600">¥{{ summary.total_cost_yuan?.toFixed(2) || '0.00' }}</p>
        <p class="text-sm text-surface-500 mt-1">总成本</p>
      </div>
      <div class="card text-center">
        <p class="text-3xl font-bold text-green-600">{{ summary.total_tokens?.toLocaleString() || 0 }}</p>
        <p class="text-sm text-surface-500 mt-1">总Token数</p>
      </div>
      <div class="card text-center">
        <p class="text-3xl font-bold text-purple-600">{{ summary.call_count || 0 }}</p>
        <p class="text-sm text-surface-500 mt-1">调用次数</p>
      </div>
    </div>

    <div class="card">
      <h2 class="text-lg font-semibold mb-4">📊 模型成本分布</h2>
      <div v-if="Object.keys(summary.model_breakdown || {}).length === 0" class="text-center py-8 text-surface-400">暂无数据</div>
      <div v-else class="space-y-3">
        <div v-for="(data, model) in summary.model_breakdown" :key="model" class="flex items-center gap-4 p-3 rounded-lg bg-surface-50">
          <div class="flex-1">
            <p class="font-medium">{{ model }}</p>
            <p class="text-sm text-surface-500">{{ data.calls }} 次调用 · {{ data.tokens.toLocaleString() }} tokens</p>
          </div>
          <p class="text-lg font-bold text-primary-600">¥{{ data.cost.toFixed(4) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { observabilityApi } from '@/api/modules/observability'
import type { CostSummary } from '@/types'

const summary = ref<CostSummary>({ total_cost_yuan: 0, total_tokens: 0, call_count: 0, model_breakdown: {} })

onMounted(async () => {
  try {
    const res = await observabilityApi.getCost()
    summary.value = res.data
  } catch {}
})
</script>