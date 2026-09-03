import { ref, onUnmounted } from 'vue'

export function usePolling(fn: () => Promise<void>, interval = 3000) {
  const isActive = ref(false)
  let timer: ReturnType<typeof setInterval> | null = null

  function start() {
    if (isActive.value) return
    isActive.value = true
    fn()
    timer = setInterval(fn, interval)
  }

  function stop() {
    isActive.value = false
    if (timer) { clearInterval(timer); timer = null }
  }

  onUnmounted(stop)
  return { isActive, start, stop }
}