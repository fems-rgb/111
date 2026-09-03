import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' }
})

client.interceptors.request.use(config => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

let isRefreshing = false
let failedQueue: Array<{ resolve: Function; reject: Function }> = []

client.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => client(originalRequest))
      }
      originalRequest._retry = true
      isRefreshing = true
      const authStore = useAuthStore()
      if (authStore.refreshToken) {
        try {
          const res = await axios.post('/api/v1/auth/refresh', { refresh_token: authStore.refreshToken })
          authStore.setToken(res.data.access_token)
          failedQueue.forEach(({ resolve }) => resolve())
          failedQueue = []
          originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`
          return client(originalRequest)
        } catch {
          failedQueue.forEach(({ reject }) => reject())
          failedQueue = []
          authStore.logout()
        } finally {
          isRefreshing = false
        }
      } else {
        authStore.logout()
      }
    }
    return Promise.reject(error)
  }
)

export default client