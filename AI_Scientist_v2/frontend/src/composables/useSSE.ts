import { ref, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

export interface SSEEvent {
  type: string
  project_id?: number
  [key: string]: any
}

export function useSSE(initialSteps?: Array<{agent_name: string; display_name?: string; status?: string; step_order?: number}>, filterProjectId?: number) {
  const connected = ref(false)
  const events = ref<SSEEvent[]>([])
  const pipelineSteps = ref<Array<{agent_name: string; display_name?: string; status: string; step_order: number; version?: number; elapsed?: number; reason?: string}>>(
    initialSteps?.map((s, i) => ({
      agent_name: s.agent_name,
      display_name: s.display_name,
      status: s.status || 'pending',
      step_order: s.step_order ?? i + 1
    })) || []
  )
  let source: EventSource | null = null
  let retryCount = 0
  const MAX_RETRIES = 10

  function connect() {
    const authStore = useAuthStore()
    if (!authStore.token || source) return

    source = new EventSource(`/api/v1/stream/events?token=${authStore.token}`)

    source.onopen = () => {
      connected.value = true
      retryCount = 0
      console.log('[SSE] 连接成功')
    }

    source.onmessage = (e) => {
      try {
        const data: SSEEvent = JSON.parse(e.data)
        // 如果指定了 project_id 过滤，只处理匹配的事件
        if (filterProjectId && data.project_id && data.project_id !== filterProjectId) return
        events.value.push(data)
        handleEvent(data)
      } catch {}
    }

    source.onerror = () => {
      connected.value = false
      source?.close()
      source = null
      retryCount++
      if (retryCount > MAX_RETRIES) {
        console.warn('[SSE] max retries reached, stopping')
        return
      }
      const delay = Math.min(5000 * Math.pow(2, retryCount - 1), 60000)
      console.warn('[SSE] retry ' + retryCount + ', wait ' + (delay/1000) + 's')
      setTimeout(connect, delay)
    }
  }

  function handleEvent(data: SSEEvent) {
    const appStore = useAppStore()
    switch (data.type) {
      case 'agent.step_update': {
        const step = data as any
        const idx = pipelineSteps.value.findIndex(s => s.agent_name === step.agent_name)
        if (idx >= 0) {
          pipelineSteps.value[idx].status = step.status
          if (step.display_name) pipelineSteps.value[idx].display_name = step.display_name
        } else {
          pipelineSteps.value.push({
            agent_name: step.agent_name,
            display_name: step.display_name,
            status: step.status,
            step_order: step.step_order || pipelineSteps.value.length + 1
          })
          pipelineSteps.value.sort((a, b) => a.step_order - b.step_order)
        }
        break
      }
      case 'agent.completed': {
        const cs = data as any
        const ci = pipelineSteps.value.findIndex(s => s.agent_name === cs.agent_name || s.agent_name === (cs as any).name)
        if (ci >= 0) pipelineSteps.value[ci].status = 'completed'
        appStore.showToast(`✅ Agent ${data.agent_name || ''} 执行完成`, 'success')
        break
      }
      case 'agent.failed':
        appStore.showToast(`❌ Agent执行失败: ${data.error || ''}`, 'error')
        break
      case 'agent.review_needed': {
        // 更新步骤状态为 waiting_review
        const rn = data as any
        const ri = pipelineSteps.value.findIndex(s => s.agent_name === rn.agent_name)
        if (ri >= 0) pipelineSteps.value[ri].status = 'waiting_review'
        appStore.showToast(`⏸️ 需要人工审核: ${data.agent_name || ''}`, 'info')
        break
      }
      case 'project.completed':
        appStore.showToast('🎉 项目研究完成！', 'success')
        break
      case 'project.failed':
        appStore.showToast('❌ 项目执行失败', 'error')
        break
    }
  }

  /** 外部同步：用服务端真实任务状态覆盖本地（用于初始加载或轮询刷新） */
  function syncFromTasks(tasks: Array<{agent_name: string; status: string; display_name?: string; step_order?: number; error_message?: string}>) {
    if (!tasks || tasks.length === 0) return
    pipelineSteps.value = tasks.map((t, i) => ({
      agent_name: t.agent_name,
      display_name: t.display_name,
      status: t.status,
      step_order: t.step_order ?? i + 1,
      reason: t.error_message
    }))
  }

  function disconnect() {
    source?.close()
    source = null
    connected.value = false
  }

  onUnmounted(disconnect)

  return { connected, events, pipelineSteps, connect, disconnect, syncFromTasks }
}
