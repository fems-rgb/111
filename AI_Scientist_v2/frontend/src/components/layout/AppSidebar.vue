<template>
  <aside :class="['bg-white border-r border-surface-200 flex flex-col transition-all duration-300', appStore.sidebarCollapsed ? 'w-16' : 'w-64']">
    <!-- Logo -->
    <div class="h-16 flex items-center px-4 border-b border-surface-100">
      <span class="text-2xl">🧠</span>
      <span v-if="!appStore.sidebarCollapsed" class="ml-3 font-bold text-lg bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">智研星枢</span>
    </div>

    <!-- 导航 -->
    <nav class="flex-1 p-3 space-y-1 overflow-y-auto">
      <router-link v-for="item in navItems" :key="item.path" :to="item.path"
                   :class="[$route.path === item.path ? 'sidebar-link-active' : 'sidebar-link']"
                   :title="appStore.sidebarCollapsed ? item.label : ''">
        <span class="text-lg relative">{{ item.icon }}<span v-if="item.badge" class="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span></span>
        <span v-if="!appStore.sidebarCollapsed">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- 底部用户区 -->
    <div class="p-3 border-t border-surface-100">
      <router-link to="/settings"
        class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-surface-50 transition-colors cursor-pointer group">
        <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-medium text-sm group-hover:ring-2 ring-primary-300 transition-all">
          {{ authStore.displayName?.charAt(0)?.toUpperCase() || 'U' }}
        </div>
        <div v-if="!appStore.sidebarCollapsed" class="flex-1 min-w-0">
          <p class="text-sm font-medium truncate">{{ authStore.displayName }}</p>
          <p class="text-xs text-surface-400 truncate">{{ authStore.user?.role }}</p>
        </div>
        <span v-if="!appStore.sidebarCollapsed" class="text-surface-300 group-hover:text-primary-500 transition-colors">⚙️</span>
      </router-link>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { getExperimentHistory } from '@/api/modules/experiment'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const appStore = useAppStore()
const authStore = useAuthStore()

const expRunning = ref(false)
let _expTimer: any = null
async function _pollExp() {
  try {
    const r = await getExperimentHistory({ page: 1, page_size: 1 })
    const items = r.data?.items || []
    expRunning.value = items.length > 0 && items[0].status === 'running'
  } catch {}
}
onMounted(() => { _pollExp(); _expTimer = setInterval(_pollExp, 5000) })
onUnmounted(() => { if (_expTimer) clearInterval(_expTimer) })

const navItems = computed(() => {
  const items = [
    { path: '/', icon: '📊', label: '工作台' },
    { path: '/chat', icon: '💬', label: 'AI对话' },
    { path: '/knowledge', icon: '📚', label: '资料库' },
    { path: '/questions', icon: '🔬', label: '科学问题题库' },
    { path: '/experiment-lab', icon: '🧪', label: '实验模拟场', badge: expRunning.value },
    { path: '/skills', icon: '🛜', label: '技能市场' },
    { path: '/automation', icon: '⚡', label: '自动化流水线' },
    { path: '/agents', icon: '🤖', label: 'Agent中心' },
    { path: '/traces', icon: '🔍', label: '追踪回放' },
    { path: '/cost', icon: '💵', label: '成本分析' },
  ]
  if (authStore.isAdmin) {
    items.push({ path: '/admin', icon: '🛡️', label: '管理后台' })
  }
  return items
})
</script>