import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { authApi } from '@/api/modules/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string>(localStorage.getItem('token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refreshToken') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const displayName = computed(() => user.value?.display_name || user.value?.username || '')

  function setToken(t: string, rt?: string) {
    token.value = t
    localStorage.setItem('token', t)
    if (rt) {
      refreshToken.value = rt
      localStorage.setItem('refreshToken', rt)
    }
  }

  async function init() {
    if (token.value) {
      try {
        const res = await authApi.getMe()
        user.value = res.data
      } catch {
        logout()
      }
    }
  }

  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    setToken(res.data.access_token, res.data.refresh_token)
    user.value = res.data.user
  }

  async function register(data: { username: string; email: string; password: string; display_name?: string; role?: string; institution?: string }) {
    const res = await authApi.register(data)
    setToken(res.data.access_token, res.data.refresh_token)
    user.value = res.data.user
  }

  function logout() {
    user.value = null
    token.value = ''
    refreshToken.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  return { user, token, refreshToken, isLoggedIn, isAdmin, displayName, setToken, init, login, register, logout }
})