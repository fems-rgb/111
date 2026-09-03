<template>
  <div class="space-y-6 animate-fade-in">
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">🔍 全链路追踪</h2>
        <button @click="fetchTraces" class="btn-secondary text-sm">刷新</button>
      </div>
      <div v-if="loading" class="text-center py-8 text-surface-400">加载中...</div>
      <div v-else-if="traces.length === 0" class="text-center py-8 text-surface-400">暂无追踪记录</div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-surface-200">
              <th class="text-left py-3 px-3 font-medium text-surface-600">时间</th>
              <th class="text-left py-3 px-3 font-medium text-surface-600">类型</th>
              <th class="text-left py-3 px-3 font-medium text-surface-600">名称</th>
              <th class="text-left py-3 px-3 font-medium text-surface-600">状态</th>
              <th class="text-left py-3 px-3 font-medium text-surface-600">耗时</th>
              <th class="text-left py-3 px-3 font-medium text-surface-600">Tokens</th>
              <th class="text-left py-3 px-3 font-medium text-surface-600">成本</th>
              <th class="text-left py-3 px-3 font-medium text-surface-600">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="trace in traces" :key="trace.span_id" class="border-b border-surface-100 hover:bg-surface-50">
              <td class="py-3 px-3 text-surface-500">{{ new Date(trace.created_at).toLocaleTimeString('zh-CN') }}</td>
              <td class="py-3 px-3"><span class="badge-info">{{ trace.span_type }}</span></td>
              <td class="py-3 px-3 font-medium">{{ trace.span_name }}</td>
              <td class="py-3 px-3"><StatusBadge :status="trace.status" /></td>
              <td class="py-3 px-3">{{ trace.duration_ms }}ms</td>
              <td class="py-3 px-3">{{ trace.tokens_used }}</td>
              <td class="py-3 px-3">¥{{ trace.cost_yuan.toFixed(4) }}</td>
              <td class="py-3 px-3">
                <button @click="selectedTrace = trace" class="text-primary-600 hover:underline text-xs">详情</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 追踪详情弹窗 -->
    <div v-if="selectedTrace" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="selectedTrace = null">
      <div class="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">{{ selectedTrace.span_name }}</h3>
          <button @click="selectedTrace = null" class="text-surface-400 hover:text-surface-600 text-xl">✕</button>
        </div>
        <div class="space-y-4">
          <div><p class="text-sm font-medium text-surface-500 mb-1">输入</p><pre class="bg-surface-50 p-3 rounded-lg text-xs overflow-x-auto max-h-40">{{ selectedTrace.input_data }}</pre></div>
          <div><p class="text-sm font-medium text-surface-500 mb-1">输出</p><pre class="bg-surface-50 p-3 rounded-lg text-xs overflow-x-auto max-h-40">{{ selectedTrace.output_data }}</pre></div>
          <div v-if="selectedTrace.error_detail"><p class="text-sm font-medium text-red-500 mb-1">错误</p><pre class="bg-red-50 p-3 rounded-lg text-xs text-red-700">{{ selectedTrace.error_detail }}</pre></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { observabilityApi } from '@/api/modules/observability'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { TraceRecord } from '@/types'

const traces = ref<TraceRecord[]>([])
const loading = ref(false)
const selectedTrace = ref<TraceRecord | null>(null)

async function fetchTraces() {
  loading.value = true
  try {
    const res = await observabilityApi.getTraces(undefined, 100)
    traces.value = res.data
  } finally { loading.value = false }
}

onMounted(fetchTraces)
</script>