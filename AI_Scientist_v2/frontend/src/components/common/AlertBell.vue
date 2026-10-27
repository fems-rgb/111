<template>
  <!-- 预警铃铛：60s 轮询 /alerts；未读角标 + 按严重度分组的下拉面板 -->
  <div ref="rootEl" class="relative" v-if="authStore.isLoggedIn">
    <button @click="toggle" title="预警中心"
            class="relative p-2 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg transition-colors">
      <span class="text-lg">🔔</span>
      <span v-if="alerts.length"
            class="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-0.5 rounded-full text-[10px] font-bold text-white flex items-center justify-center"
            :class="hasError ? 'bg-red-500' : 'bg-amber-400'">{{ alerts.length }}</span>
    </button>

    <div v-if="open" @click.stop
         class="absolute right-0 top-10 w-80 max-h-96 overflow-y-auto bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-600 rounded-xl shadow-lg z-50 p-2">
      <p class="px-2 py-1 text-xs font-semibold text-surface-500">预警中心（{{ alerts.length }}）</p>
      <p v-if="!alerts.length" class="px-2 py-4 text-sm text-surface-400 text-center">一切正常 ✅</p>
      <template v-for="sev in ['error', 'warning', 'info']" :key="sev">
        <div v-if="grouped[sev].length">
          <p class="px-2 pt-2 pb-1 text-[10px] uppercase tracking-wide text-surface-400">{{ sevLabel[sev] }}</p>
          <div v-for="a in grouped[sev]" :key="a.id"
               class="px-2 py-1.5 rounded-lg hover:bg-surface-50 dark:hover:bg-surface-700">
            <p class="text-xs font-medium text-surface-700 dark:text-surface-200">
              {{ sevIcon[sev] }} {{ a.title }}
            </p>
            <p class="text-[11px] text-surface-500 dark:text-surface-400 leading-snug mt-0.5">{{ a.message }}</p>
            <button v-if="a.action_href" @click="go(a.action_href)"
                    class="mt-1 text-[11px] text-primary-600 hover:underline">{{ a.action_label || '查看详情' }} →</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { alertsApi, type AlertItem } from '@/api/modules/alerts'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const POLL_MS = 60000
const TOAST_COOLDOWN_MS = 6 * 3600_000
// 模块级去重：AppHeader 随路由重新挂载，组件内 Set 会丢，导致每次切页面都重复弹同一个 error toast
const toastedAt = new Map<string, number>()

const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

const alerts = ref<AlertItem[]>([])
const open = ref(false)
const rootEl = ref<HTMLElement | null>(null)
let timer: number | null = null

const sevIcon = { error: '🔴', warning: '🟠', info: '🔵' } as Record<string, string>
const sevLabel = { error: '需处理', warning: '需注意', info: '供参考' } as Record<string, string>

const grouped = computed(() => {
  const g: Record<string, AlertItem[]> = { error: [], warning: [], info: [] }
  for (const a of alerts.value) {
    const list = g[a.severity] || g.info
    list.push(a)
  }
  return g
})
const hasError = computed(() => alerts.value.some(a => a.severity === 'error'))

async function poll() {
  try {
    const r = await alertsApi.list()
    alerts.value = r.data?.alerts || []
    // error 级首次出现 toast 一次；同一 id 6h 冷却跨挂载生效，不重复打扰
    const now = Date.now()
    for (const a of alerts.value) {
      if (a.severity !== 'error') continue
      const last = toastedAt.get(a.id)
      if (last !== undefined && now - last < TOAST_COOLDOWN_MS) continue
      toastedAt.set(a.id, now)
      appStore.showToast(`⚠️ ${a.title}`, 'error')
    }
  } catch { /* 静默：预警不打扰主流程 */ }
}

function toggle() { open.value = !open.value }
function go(href: string) { open.value = false; router.push(href) }
function close(e: MouseEvent) {
  // 组件内点击（铃铛/面板）不关；外部点击关闭
  if (open.value && rootEl.value && !rootEl.value.contains(e.target as Node)) open.value = false
}

onMounted(() => {
  poll()
  timer = window.setInterval(poll, POLL_MS)
  window.addEventListener('click', close)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
  window.removeEventListener('click', close)
})
</script>
