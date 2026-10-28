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

      <!-- 免费模型·填 key 即用（未配密钥的供应商：管理员可在此直接填 key 启用） -->
      <template v-if="locked.length">
        <div class="mt-1 border-t border-surface-100 dark:border-surface-700 pt-1">
          <p class="px-3 py-1 text-[10px] uppercase tracking-wide text-surface-400">🔓 更多免费模型 · 填 key 即用</p>
          <div v-for="lp in locked" :key="lp.provider" class="px-3 py-1.5">
            <div class="flex items-center justify-between gap-2">
              <p class="text-[11px] font-medium text-surface-500 dark:text-surface-300 truncate">
                {{ lp.label }} <span class="text-[10px] text-surface-400">· {{ lp.models.length }} 个模型</span>
              </p>
              <button v-if="isAdmin" @click.stop="toggleEdit(lp.provider)"
                      class="shrink-0 text-[10px] px-1.5 py-0.5 rounded border border-primary-200 text-primary-600 hover:bg-primary-50 dark:border-primary-700 dark:hover:bg-surface-700">
                {{ editing === lp.provider ? '收起' : '🔑 填 Key' }}
              </button>
            </div>
            <p class="text-[10px] text-surface-400 leading-snug">{{ lp.hint }}</p>
            <p v-if="editing !== lp.provider" class="text-[10px] text-primary-600/80 font-mono">.env → {{ lp.env_key }}</p>
            <div v-if="editing === lp.provider" class="mt-1.5">
              <div class="flex items-center gap-1">
                <input v-model="keyInput" type="password" autocomplete="off" spellcheck="false"
                       :placeholder="`粘贴 ${lp.label} 的 API Key`"
                       class="flex-1 min-w-0 text-[11px] px-2 py-1 rounded border border-surface-200 dark:border-surface-600 bg-white dark:bg-surface-700 text-surface-700 dark:text-surface-100 outline-none focus:border-primary-400"
                       @click.stop @keydown.stop @keyup.enter="saveKey(lp)" />
                <button @click.stop="saveKey(lp)" :disabled="saving"
                        class="shrink-0 text-[10px] px-2 py-1 rounded bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50">
                  {{ saving ? '保存中…' : '保存' }}
                </button>
              </div>
              <p v-if="keyErr" class="mt-1 text-[10px] text-red-500 leading-snug">{{ keyErr }}</p>
              <p class="mt-1 text-[10px] text-surface-400 leading-snug">保存后立即生效、无需重启；密钥只写不读，不会回显。</p>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { coursewareApi, providerApi, type GenerateModelItem, type LockedProvider } from '@/api/modules/courses'

interface Opt extends GenerateModelItem {
  provider_label?: string
}

const appStore = useAppStore()
const authStore = useAuthStore()
const models = ref<Opt[]>([])
const locked = ref<LockedProvider[]>([])
const open = ref(false)
const rootEl = ref<HTMLElement | null>(null)
// 填 key 交互：同一时间只展开一个供应商，避免一屏多个输入框
const editing = ref('')
const keyInput = ref('')
const keyErr = ref('')
const saving = ref(false)
// 仅管理员能改（写的是整台部署的密钥）
const isAdmin = computed(() => authStore.isAdmin)

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

function toggleEdit(pid: string) {
  editing.value = editing.value === pid ? '' : pid
  keyInput.value = ''
  keyErr.value = ''
}

async function reloadModels() {
  try {
    const r = await coursewareApi.generateModels()
    models.value = r.data?.items || []
    locked.value = r.data?.locked || []
  } catch { /* 拉不到就保持现状，不打断用户 */ }
}

async function saveKey(lp: LockedProvider) {
  const k = keyInput.value.trim()
  if (k.length < 4) { keyErr.value = '请粘贴完整的 API Key'; return }
  saving.value = true
  keyErr.value = ''
  try {
    const r = await providerApi.saveKey(lp.provider, k)
    const unlocked = r.data?.unlocked?.length || 0
    appStore.showToast(`🔓 已启用 ${lp.label}${unlocked ? `，新增 ${unlocked} 个模型` : ''}`, 'success')
    editing.value = ''
    keyInput.value = ''
    await reloadModels()
  } catch (e: any) {
    const st = e?.response?.status
    keyErr.value = st === 403
      ? '只有管理员可以修改密钥'
      : (e?.response?.data?.detail || '保存失败，请检查 Key 后重试')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await reloadModels()
  window.addEventListener('click', close)
})
onUnmounted(() => window.removeEventListener('click', close))
</script>
