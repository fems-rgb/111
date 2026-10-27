<template>
  <!-- 全局模型左右切换器：◀ 自动/模型名 ▶；选择存 appStore.preferredModel，
       各生成请求按 面板显式选择 > 此处首选 > 模式定档 的优先级使用 -->
  <div v-if="options.length > 1"
       class="flex items-center rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-800 overflow-hidden">
    <button @click="step(-1)" title="上一个模型"
            class="px-1.5 py-1 text-xs text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">◀</button>
    <span class="px-1 text-xs font-medium text-surface-700 dark:text-surface-200 whitespace-nowrap max-w-[9rem] truncate"
          :title="currentTitle">{{ currentLabel }}</span>
    <button @click="step(1)" title="下一个模型"
            class="px-1.5 py-1 text-xs text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">▶</button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { coursewareApi, type GenerateModelItem } from '@/api/modules/courses'

const appStore = useAppStore()
const models = ref<GenerateModelItem[]>([])

// 第一项固定为「自动」：不指定模型，由后端按快速/专家模式定档
const options = computed(() => [
  { value: '', label: '🤖 自动', provider: '' },
  ...models.value.map(m => ({ value: m.value, label: m.label, provider: m.provider_label || '' })),
])

const idx = computed(() => {
  const i = options.value.findIndex(o => o.value === appStore.preferredModel)
  return i < 0 ? 0 : i
})
const currentLabel = computed(() => options.value[idx.value]?.label ?? '自动')
const currentTitle = computed(() => {
  const o = options.value[idx.value]
  return o && o.value ? `${o.provider ? o.provider + ' · ' : ''}${o.label}（左右切换全局生成模型）` : '按快速/专家模式自动定档'
})

function step(dir: number) {
  const n = options.value.length
  const next = (idx.value + dir + n) % n
  const o = options.value[next]
  appStore.setPreferredModel(o.value)
  appStore.showToast(
    o.value
      ? `🧠 全局模型：${o.provider ? o.provider + ' · ' : ''}${o.label}（各生成入口默认使用，面板里显式选择优先）`
      : '🤖 已恢复自动定档：快速模式用均衡档、专家模式用强力档',
    'success',
  )
}

onMounted(async () => {
  try {
    const r = await coursewareApi.generateModels()
    models.value = r.data?.items || []
  } catch { /* 拉不到列表就整体隐藏，不打扰 */ }
})
</script>
