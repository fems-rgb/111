<template>
  <!-- 全局模型选择器：点击名称展开分组下拉直接选，◀▶ 保留快速循环；选择存 appStore.preferredModel，
       各生成请求按 面板显式选择 > 此处首选 > 模式定档 的优先级使用 -->
  <div v-if="options.length > 1" ref="rootEl" class="relative">
    <div class="flex items-center rounded-lg border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-800 overflow-hidden">
      <button @click="step(-1)" title="上一个模型"
              class="px-1.5 py-1 text-xs text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">◀</button>
      <button @click="open = !open" :title="currentTitle"
              class="px-1 py-1 text-xs font-medium text-surface-700 dark:text-surface-200 whitespace-nowrap max-w-[11rem] truncate hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
        {{ currentLabel }} <span class="text-[9px] text-surface-400">{{ open ? '▲' : '▼' }}</span>
      </button>
      <button @click="step(1)" title="下一个模型"
              class="px-1.5 py-1 text-xs text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">▶</button>
    </div>

    <div v-if="open"
         class="absolute right-0 top-9 w-72 max-h-96 overflow-y-auto bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-600 rounded-xl shadow-lg z-50 py-1">
      <p class="px-3 py-1 text-[10px] uppercase tracking-wide text-surface-400">全局生成模型</p>
      <template v-for="sec in sections" :key="sec.label">
        <div v-if="sec.items.length">
          <p v-if="sec.label" class="px-3 pt-1.5 pb-0.5 text-[10px] font-semibold text-surface-400">{{ sec.label }}</p>
          <button v-for="o in sec.items" :key="o.value"
                  @click="choose(o)"
                  class="w-full text-left px-3 py-1.5 hover:bg-surface-50 dark:hover:bg-surface-700"
                  :class="{ 'bg-primary-50 dark:bg-surface-700/60': o.value === appStore.preferredModel }">
            <span class="flex items-center gap-1 text-xs"
                  :class="o.value === appStore.preferredModel ? 'font-semibold text-primary-600' : 'text-surface-700 dark:text-surface-200'">
              <span class="w-4 shrink-0">{{ o.value === appStore.preferredModel ? '✓' : '' }}</span>
              <span class="truncate">{{ o.label }}</span>
              <span v-if="o.is_default" class="shrink-0 text-[9px] px-1 rounded bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400">默认</span>
              <span v-if="o.unavailable" class="shrink-0 text-[9px] px-1 rounded bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400">暂限流</span>
            </span>
            <span v-if="o.desc" class="block pl-5 mt-0.5 text-[10px] text-surface-400 leading-snug">{{ o.desc }}</span>
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { coursewareApi, type GenerateModelItem } from '@/api/modules/courses'

interface Opt extends GenerateModelItem {
  provider_label?: string
}

const appStore = useAppStore()
const models = ref<Opt[]>([])
const open = ref(false)
const rootEl = ref<HTMLElement | null>(null)

// 第一项固定为「自动」：不指定模型，由后端按快速/专家模式定档
const autoOpt: Opt = { value: '', label: '🤖 自动（按模式定档）', desc: '快速模式用最省的 qwen-turbo、专家模式用 qwen-max，后端自动选择', is_default: false }
const options = computed<Opt[]>(() => [autoOpt, ...models.value])

// 下拉按供应商分组；「自动」单独一节
const sections = computed(() => {
  const byProvider = new Map<string, Opt[]>()
  for (const m of models.value) {
    const k = m.provider_label || '其他'
    if (!byProvider.has(k)) byProvider.set(k, [])
    byProvider.get(k)!.push(m)
  }
  return [{ label: '', items: [autoOpt] }, ...[...byProvider].map(([label, items]) => ({ label, items }))]
})

const idx = computed(() => {
  const i = options.value.findIndex(o => o.value === appStore.preferredModel)
  return i < 0 ? 0 : i
})
const currentLabel = computed(() => (idx.value === 0 ? '🤖 自动' : options.value[idx.value]?.label ?? '自动'))
const currentTitle = computed(() => {
  const o = options.value[idx.value]
  return o && o.value
    ? `${o.provider_label ? o.provider_label + ' · ' : ''}${o.label}（点击选择，左右快速切换）`
    : '按快速/专家模式自动定档（点击选择模型）'
})

function toastFor(o: Opt) {
  appStore.showToast(
    o.value
      ? `🧠 全局模型：${o.provider_label ? o.provider_label + ' · ' : ''}${o.label}（各生成入口默认使用，面板里显式选择优先）`
      : '🤖 已恢复自动定档：快速模式用最省的 qwen-turbo、专家模式用强力档 qwen-max',
    'success',
  )
}

function choose(o: Opt) {
  appStore.setPreferredModel(o.value)
  open.value = false
  toastFor(o)
}

function step(dir: number) {
  const n = options.value.length
  const next = (idx.value + dir + n) % n
  const o = options.value[next]
  appStore.setPreferredModel(o.value)
  toastFor(o)
}

function close(e: MouseEvent) {
  if (open.value && rootEl.value && !rootEl.value.contains(e.target as Node)) open.value = false
}

onMounted(async () => {
  try {
    const r = await coursewareApi.generateModels()
    models.value = r.data?.items || []
  } catch { /* 拉不到列表就整体隐藏，不打扰 */ }
  window.addEventListener('click', close)
})
onUnmounted(() => window.removeEventListener('click', close))
</script>
