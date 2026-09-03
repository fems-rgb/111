<template>

  <div class="max-w-4xl mx-auto space-y-4 animate-fade-in">
    <div class="card">
      <h2 class="text-lg font-semibold mb-3 flex items-center"><span class="mr-2">🎨</span> 外观主题</h2>
      <div class="mb-4"><label class="block text-sm font-medium mb-1">字体大小</label><input type="range" v-model="fontSize" min="12" max="20" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer" /><div class="flex justify-between text-xs text-gray-500 mt-1"><span>12px</span><span>{{ fontSize }}px</span><span>20px</span></div></div>
      <div class="mb-4"><label class="block text-sm font-medium mb-1">深色模式</label><div class="flex space-x-3"><button v-for="item in modeOptions" :key="item.value" @click="mode = item.value" :class="['px-3 py-1.5 rounded-md text-sm font-medium transition-colors', mode === item.value ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200']">{{ item.label }}</button></div></div>
      <div class="mb-3"><label class="block text-sm font-medium mb-1">紧凑模式 <span class="ml-2 text-xs text-gray-500">(减小间距)</span></label><div class="flex items-center"><input type="checkbox" v-model="compactMode" class="h-4 w-4 text-blue-600 rounded focus:ring-blue-500" /><span class="ml-2 text-sm text-gray-700">启用紧凑布局</span></div></div>
      <p class="text-xs text-gray-400 pt-1">💡 以上设置即时生效，自动保存到本地</p>
    </div>

    <div class="card">
      <h2 class="text-lg font-semibold mb-4">⚙️ 个人设置</h2>
      <form @submit.prevent="handleSave" class="space-y-3">
        <div>
          <label class="block text-sm font-medium text-surface-700 mb-1">显示名称</label>
          <input v-model="form.display_name" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 mb-1">机构/学校</label>
          <input v-model="form.institution" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 mb-1">个人简介</label>
          <textarea v-model="form.bio" class="input-field h-24 resize-none"></textarea>
        </div>
        <button type="submit" :disabled="saving" class="btn-primary">{{ saving ? '保存中...' : '保存' }}</button>
      </form>
    </div>

    <div class="card">
      <h2 class="text-lg font-semibold mb-4">👤 账号信息</h2>
      <div class="space-y-2 text-sm">
        <p><span class="text-surface-500">用户名：</span>{{ authStore.user?.username }}</p>
        <p><span class="text-surface-500">邮箱：</span>{{ authStore.user?.email }}</p>
        <p><span class="text-surface-500">角色：</span>{{ authStore.user?.role }}</p>
        <p><span class="text-surface-500">注册时间：</span>{{ authStore.user?.created_at }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/modules/auth'

const authStore = useAuthStore()
const appStore = useAppStore()
const saving = ref(false)
// ===== 外观设置 =====
const fontSize = ref(parseInt(localStorage.getItem('fontSize') || '14'))
const mode = ref(localStorage.getItem('darkMode') || 'system')
const compactMode = ref(localStorage.getItem('compactMode') === 'true')
const modeOptions = [
  { label: '浅色', value: 'light' },
  { label: '深色', value: 'dark' },
  { label: '跟随系统', value: 'system' }
]

function applyDarkMode(m: string) {
  const root = document.documentElement
  if (m === 'dark') root.classList.add('dark')
  else if (m === 'light') root.classList.remove('dark')
  else window.matchMedia('(prefers-color-scheme: dark)').matches ? root.classList.add('dark') : root.classList.remove('dark')
}

watch(fontSize, (v) => {
  localStorage.setItem('fontSize', String(v))
  document.documentElement.style.fontSize = v + 'px'
})
watch(mode, (v) => { localStorage.setItem('darkMode', v); applyDarkMode(v) })
watch(compactMode, (v) => { localStorage.setItem('compactMode', String(v)) })

onMounted(() => {
  applyDarkMode(mode.value)
  document.documentElement.style.fontSize = fontSize.value + 'px'
})

const form = reactive({ display_name: '', institution: '', bio: '' })

onMounted(() => {
  if (authStore.user) {
    form.display_name = authStore.user.display_name
    form.institution = authStore.user.institution
    form.bio = authStore.user.bio
  }
})

async function handleSave() {
  saving.value = true
  try {
    await authApi.updateMe(form)
    appStore.showToast('保存成功', 'success')
    await authStore.init()
  } catch (e: any) {
    appStore.showToast('保存失败', 'error')
  } finally { saving.value = false }
}
</script>