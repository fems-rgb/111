<template>
  <header class="h-16 bg-white dark:bg-surface-900 border-b border-surface-200 dark:border-surface-700 flex items-center justify-between px-6 transition-colors">
    <div class="flex items-center gap-4">
      <button @click="appStore.toggleSidebar()" class="p-2 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg transition-colors">
        <span class="text-lg">☰</span>
      </button>
      <h1 class="text-lg font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
        🧪 智研星枢
      </h1>
      <span class="text-xs text-surface-400 hidden md:inline">v3.0 · AI Scientist</span>
    </div>

    <div class="flex items-center gap-3">
      <!-- ✅ 工作空间选择器（联动 store） -->
      <select v-model="appStore.currentWorkspace"
              @change="onWorkspaceChange"
              class="text-xs py-1.5 px-2 border border-surface-200 dark:border-surface-600 rounded-lg bg-white dark:bg-surface-800 text-surface-700 dark:text-surface-200 focus:ring-2 focus:ring-primary-500 outline-none w-36 hidden md:block">
        <option value="personal">🏠 个人空间</option>
        <option value="lab">🔬 实验室</option>
        <option value="classroom">📚 课堂</option>
        <option value="enterprise">🏢 企业研发</option>
      </select>

      <!-- 权限指示 -->
      <span :class="['text-xs px-2 py-0.5 rounded-full font-medium',
        permissionLevel === 'admin' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
        permissionLevel === 'teacher' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
        'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400']">
        {{ permissionLabel }}
      </span>

      <span class="text-sm text-surface-500 dark:text-surface-400 hidden sm:inline">{{ new Date().toLocaleDateString('zh-CN') }}</span>

      <!-- 快速/专家模式 -->
      <div class="flex items-center bg-surface-100 dark:bg-surface-700 rounded-lg p-0.5">
        <button @click="appStore.setMode('quick')"
          :class="['px-3 py-1 text-xs font-medium rounded-md transition-all',
            appStore.mode === 'quick' ? 'bg-white dark:bg-surface-600 shadow-sm text-primary-600' : 'text-surface-500 dark:text-surface-400 hover:text-surface-700']">
          ⚡ 快速
        </button>
        <button @click="appStore.setMode('expert')"
          :class="['px-3 py-1 text-xs font-medium rounded-md transition-all',
            appStore.mode === 'expert' ? 'bg-white dark:bg-surface-600 shadow-sm text-accent-600' : 'text-surface-500 dark:text-surface-400 hover:text-surface-700']">
          🔬 专家
        </button>
      </div>

      <!-- ✅ 暗色模式切换 -->
      <button @click="appStore.toggleDarkMode()"
              class="p-2 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg transition-colors"
              :title="appStore.darkMode ? '切换到亮色模式' : '切换到暗色模式'">
        <span class="text-lg">{{ appStore.darkMode ? '🌙' : '☀️' }}</span>
      </button>

      <button @click="authStore.logout(); $router.push('/login')" class="btn-secondary text-sm">退出</button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

const permissionLevel = computed(() => authStore.user?.role || 'student')
const permissionLabel = computed(() => {
  const map: Record<string, string> = {
    admin: '🛡️ 管理员', teacher: '👨‍🏫 教师', researcher: '🔬 研究员', student: '🎓 学生'
  }
  return map[permissionLevel.value] || '🎓 学生'
})

function onWorkspaceChange() {
  const labels: Record<string, string> = {
    personal: '个人空间', lab: '实验室', classroom: '课堂', enterprise: '企业研发'
  }
  appStore.showToast('已切换到 ' + (labels[appStore.currentWorkspace] || appStore.currentWorkspace), 'success')
}
</script>
