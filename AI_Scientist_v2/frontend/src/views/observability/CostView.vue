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
      <h2 class="text-lg font-semibold mb-4">📈 近 30 天成本趋势与预测</h2>
      <div v-if="!history.length" class="text-center py-8 text-surface-400">暂无日成本数据（产生调用后自动积累）</div>
      <template v-else>
        <svg :viewBox="`0 0 ${chart.w} ${chart.h}`" class="w-full h-40">
          <polyline :points="historyPoints" fill="none" stroke="#6366f1" stroke-width="2" />
          <polyline v-if="forecastPoint" :points="forecastLine" fill="none" stroke="#f59e0b"
                    stroke-width="2" stroke-dasharray="4 3" />
          <circle v-if="forecastPoint" :cx="forecastPoint[0]" :cy="forecastPoint[1]" r="3.5" fill="#f59e0b" />
        </svg>
        <div v-if="forecast.status === 'ok'" class="mt-3 text-sm text-surface-600 space-y-1">
          <p>本月已花 <b>¥{{ forecast.month_spend_yuan?.toFixed(2) }}</b>，日均 ¥{{ forecast.daily_avg_yuan?.toFixed(3) }}，
            按趋势预计本月共 <b class="text-primary-600">¥{{ forecast.forecast_month_total_yuan?.toFixed(2) }}</b>
            （置信度 {{ (forecast.confidence * 100).toFixed(0) }}%）</p>
          <p v-if="forecast.exceed_threshold_in_days === 0" class="text-red-600">⚠️ 本月成本已超过预警线 ¥{{ forecast.threshold_yuan }}</p>
          <p v-else-if="forecast.exceed_threshold_in_days != null" class="text-amber-600">⚠️ 预计 {{ forecast.exceed_threshold_in_days }} 天后超过预警线 ¥{{ forecast.threshold_yuan }}</p>
          <p v-else class="text-green-600">✅ 按当前趋势，60 天内不会超过预警线 ¥{{ forecast.threshold_yuan }}</p>
        </div>
        <p v-else class="mt-3 text-xs text-surface-400">日成本数据不足 3 天，暂不给出线性预测结论。</p>
      </template>
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
import { ref, computed, onMounted } from 'vue'
import { observabilityApi } from '@/api/modules/observability'
import type { CostSummary } from '@/types'

const summary = ref<CostSummary>({ total_cost_yuan: 0, total_tokens: 0, call_count: 0, model_breakdown: {} })

// 简易 SVG 折线（零依赖）：历史实线 + 预测虚线段（下期外推点）
const chart = { w: 600, h: 140, pad: 8 }
const history = computed(() => summary.value.history || [])
const forecast = computed<any>(() => summary.value.forecast || {})
const maxVal = computed(() => Math.max(0.0001, ...history.value.map(h => h.cost_yuan)))
function xAt(i: number, n: number) {
  return chart.pad + (n <= 1 ? 0 : i * (chart.w - 2 * chart.pad) / (n - 1))
}
function yAt(v: number) {
  return chart.h - chart.pad - (v / maxVal.value) * (chart.h - 2 * chart.pad)
}
const historyPoints = computed(() =>
  history.value.map((h, i) => `${xAt(i, history.value.length).toFixed(1)},${yAt(h.cost_yuan).toFixed(1)}`).join(' '))
const forecastPoint = computed<[number, number] | null>(() => {
  const f = forecast.value
  if (f.status !== 'ok' || history.value.length < 3) return null
  const x = xAt(history.value.length - 1, history.value.length) + 36   // 虚线向前延伸一段
  return [Math.min(x, chart.w - 4), yAt(Math.min(f.predicted_daily_yuan ?? 0, maxVal.value * 1.5))]
})
const forecastLine = computed(() => {
  if (!forecastPoint.value || !history.value.length) return ''
  const last = history.value[history.value.length - 1]
  return `${xAt(history.value.length - 1, history.value.length).toFixed(1)},${yAt(last.cost_yuan).toFixed(1)} ${forecastPoint.value[0].toFixed(1)},${forecastPoint.value[1].toFixed(1)}`
})

onMounted(async () => {
  try {
    const res = await observabilityApi.getCost()
    summary.value = res.data
  } catch {}
})
</script>
