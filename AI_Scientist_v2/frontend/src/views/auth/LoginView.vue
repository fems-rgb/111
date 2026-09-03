<template>
  <div class="min-h-screen flex relative overflow-hidden">
    <!-- 动态背景粒子 -->
    <canvas ref="canvasRef" class="absolute inset-0 w-full h-full pointer-events-none z-0"></canvas>

    <!-- 左侧品牌区 -->
    <div class="hidden lg:flex lg:w-1/2 relative z-10 items-center justify-center p-12">
      <div class="absolute inset-0 bg-gradient-to-br from-primary-600/90 via-primary-700/90 to-primary-900/90 backdrop-blur-sm"></div>
      <div class="relative text-center text-white animate-slide-up">
        <div class="text-7xl mb-6 animate-bounce-slow">🏛️</div>
        <h1 class="text-5xl font-bold mb-4 tracking-tight">智研星枢</h1>
        <p class="text-xl opacity-90 mb-2 animate-fade-in-up">基于国产开源大模型的</p>
        <p class="text-xl opacity-90 mb-8 animate-fade-in-up animation-delay-500">多智能体人文社科科研平台</p>
        <div class="flex gap-3 justify-center text-sm opacity-80 flex-wrap">
          <span class="px-4 py-1.5 bg-white/20 rounded-full backdrop-blur-md border border-white/10 hover:bg-white/30 transition-all">📖 文献综述</span>
          <span class="px-4 py-1.5 bg-white/20 rounded-full backdrop-blur-md border border-white/10 hover:bg-white/30 transition-all">📐 研究设计</span>
          <span class="px-4 py-1.5 bg-white/20 rounded-full backdrop-blur-md border border-white/10 hover:bg-white/30 transition-all">📊 数据分析</span>
          <span class="px-4 py-1.5 bg-white/20 rounded-full backdrop-blur-md border border-white/10 hover:bg-white/30 transition-all">✍️ 学术写作</span>
          <span class="px-4 py-1.5 bg-white/20 rounded-full backdrop-blur-md border border-white/10 hover:bg-white/30 transition-all">🔍 同行评审</span>
          <span class="px-4 py-1.5 bg-white/20 rounded-full backdrop-blur-md border border-white/10 hover:bg-white/30 transition-all">🖼️ 多模态分析</span>
        </div>
        <div class="mt-10 grid grid-cols-3 gap-4 text-center">
          <div><p class="text-3xl font-bold">5</p><p class="text-xs opacity-70">专业Agent</p></div>
          <div><p class="text-3xl font-bold">12</p><p class="text-xs opacity-70">数据库表</p></div>
          <div><p class="text-3xl font-bold">72+</p><p class="text-xs opacity-70">代码文件</p></div>
        </div>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="flex-1 flex items-center justify-center p-8 bg-surface-50 dark:bg-surface-900 relative z-10">
      <div class="w-full max-w-md animate-fade-in">
        <div class="lg:hidden text-center mb-8">
          <span class="text-5xl">🏛️</span>
          <h1 class="text-3xl font-bold mt-3 bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">智研星枢</h1>
          <p class="text-surface-500 mt-1">AI驱动的人文社科科研平台</p>
        </div>

        <!-- Tab切换 -->
        <div class="flex mb-8 bg-surface-100 dark:bg-surface-800 rounded-xl p-1">
          <button @click="isLogin = true" :class="['flex-1 py-2.5 rounded-lg text-sm font-medium transition-all duration-300', isLogin ? 'bg-white dark:bg-surface-700 shadow-sm text-primary-700 dark:text-primary-400' : 'text-surface-500 dark:text-surface-400']">登录</button>
          <button @click="isLogin = false" :class="['flex-1 py-2.5 rounded-lg text-sm font-medium transition-all duration-300', !isLogin ? 'bg-white dark:bg-surface-700 shadow-sm text-primary-700 dark:text-primary-400' : 'text-surface-500 dark:text-surface-400']">注册</button>
        </div>

        <!-- 错误提示 -->
        <transition name="slide-up">
          <div v-if="error" class="mb-4 p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 text-sm flex items-center gap-2">
            <span>⚠️</span> {{ error }}
          </div>
        </transition>

        <!-- 登录表单 -->
        <form v-if="isLogin" @submit.prevent="handleLogin" class="space-y-4">
          <div class="group">
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">用户名</label>
            <div class="relative">
              <span class="absolute left-3 top-3 text-surface-400">👤</span>
              <input v-model="loginForm.username" type="text" class="input-field pl-10" placeholder="请输入用户名" required />
            </div>
          </div>
          <div class="group">
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">密码</label>
            <div class="relative">
              <span class="absolute left-3 top-3 text-surface-400">🔒</span>
              <input v-model="loginForm.password" type="password" class="input-field pl-10" placeholder="请输入密码" required />
            </div>
          </div>
          <button type="submit" :disabled="loading"
                  class="w-full py-3 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl font-medium hover:from-primary-700 hover:to-primary-800 transition-all duration-300 shadow-lg shadow-primary-500/25 disabled:opacity-50 transform hover:scale-[1.02] active:scale-[0.98]">
            {{ loading ? '⏳ 登录中...' : '🚀 登录' }}
          </button>
        </form>

        <!-- 注册表单 -->
        <form v-else @submit.prevent="handleRegister" class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">用户名</label>
              <input v-model="regForm.username" type="text" class="input-field" required />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">邮箱</label>
              <input v-model="regForm.email" type="email" class="input-field" required />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">密码</label>
            <input v-model="regForm.password" type="password" class="input-field" placeholder="至少6位" required />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">昵称</label>
              <input v-model="regForm.display_name" type="text" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">身份</label>
              <select v-model="regForm.role" class="input-field">
                <option value="student">学生</option>
                <option value="teacher">教师</option>
                <option value="researcher">研究员</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">机构/学校</label>
            <input v-model="regForm.institution" type="text" class="input-field" />
          </div>
          <button type="submit" :disabled="loading"
                  class="w-full py-3 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-xl font-medium hover:from-primary-700 hover:to-accent-700 transition-all duration-300 shadow-lg shadow-primary-500/25 disabled:opacity-50 transform hover:scale-[1.02] active:scale-[0.98]">
            {{ loading ? '⏳ 注册中...' : '✨ 注册' }}
          </button>
        </form>

        <p class="mt-6 text-center text-xs text-surface-400">默认管理员: admin / admin123456</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isLogin = ref(true)
const loading = ref(false)
const error = ref('')
const canvasRef = ref<HTMLCanvasElement | null>(null)

const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', email: '', password: '', display_name: '', role: 'student', institution: '' })

// ── 粒子背景动画 ──
let animId: number
onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')!
  let w = canvas.width = window.innerWidth
  let h = canvas.height = window.innerHeight

  const particles: { x: number; y: number; vx: number; vy: number; r: number; o: number }[] = []
  for (let i = 0; i < 80; i++) {
    particles.push({
      x: Math.random() * w, y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.5, vy: (Math.random() - 0.5) * 0.5,
      r: Math.random() * 2 + 1, o: Math.random() * 0.5 + 0.1
    })
  }

  function draw() {
    ctx.clearRect(0, 0, w, h)
    for (const p of particles) {
      p.x += p.vx; p.y += p.vy
      if (p.x < 0 || p.x > w) p.vx *= -1
      if (p.y < 0 || p.y > h) p.vy *= -1
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(59, 130, 246, ${p.o})`
      ctx.fill()
    }
    // 连线
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x
        const dy = particles[i].y - particles[j].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 120) {
          ctx.beginPath()
          ctx.moveTo(particles[i].x, particles[i].y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.strokeStyle = `rgba(59, 130, 246, ${0.1 * (1 - dist / 120)})`
          ctx.stroke()
        }
      }
    }
    animId = requestAnimationFrame(draw)
  }
  draw()

  const resize = () => { w = canvas.width = window.innerWidth; h = canvas.height = window.innerHeight }
  window.addEventListener('resize', resize)
  onUnmounted(() => { cancelAnimationFrame(animId); window.removeEventListener('resize', resize) })
})

async function handleLogin() {
  loading.value = true; error.value = ''
  try {
    await authStore.login(loginForm.username, loginForm.password)
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally { loading.value = false }
}

async function handleRegister() {
  loading.value = true; error.value = ''
  try {
    await authStore.register(regForm)
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '注册失败'
  } finally { loading.value = false }
}
</script>

<style scoped>
@keyframes bounce-slow {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
.animate-bounce-slow { animation: bounce-slow 3s ease-in-out infinite; }

@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 0.9; transform: translateY(0); }
}
.animate-fade-in-up {
  animation: fade-in-up 0.8s ease-out forwards;
  opacity: 0;
}
.animation-delay-500 {
  animation-delay: 0.5s;
}
</style>