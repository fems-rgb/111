import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import api from '@/api/client'

export interface PipelineAgent {
  name: string
  display_name: string
}

const STORAGE_KEY = 'ai_scientist_custom_pipeline'

export const usePipelineStore = defineStore('pipeline', () => {
  const selectedAgents = ref<PipelineAgent[]>([])
  const currentProjectId = ref<string | null>(null)

  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) selectedAgents.value = JSON.parse(saved)
  } catch { /* ignore */ }

  watch(selectedAgents, (val) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(val))
  }, { deep: true })

  function setAgents(agents: PipelineAgent[]) {
    selectedAgents.value = agents
  }

  function getPipelineNames(): string[] {
    return selectedAgents.value.map(a => a.name)
  }

  function clear() {
    selectedAgents.value = []
    localStorage.removeItem(STORAGE_KEY)
  }

  // ===== 流水线执行控制 API =====
  async function startPipeline(projectId: string) {
    currentProjectId.value = projectId
    const res = await api.post(`/pipeline/${projectId}/start`, {
      agents: getPipelineNames()
    })
    return res
  }

  async function retryCurrentStep() {
    if (!currentProjectId.value) throw new Error('没有活跃的流水线')
    const res = await api.post(`/pipeline/${currentProjectId.value}/retry`)
    return res
  }

  async function skipCurrentStep() {
    if (!currentProjectId.value) throw new Error('没有活跃的流水线')
    const res = await api.post(`/pipeline/${currentProjectId.value}/skip`)
    return res
  }

  async function abortPipeline() {
    if (!currentProjectId.value) throw new Error('没有活跃的流水线')
    const res = await api.post(`/pipeline/${currentProjectId.value}/abort`)
    currentProjectId.value = null
    return res
  }

  return {
    selectedAgents, currentProjectId,
    setAgents, getPipelineNames, clear,
    startPipeline, retryCurrentStep, skipCurrentStep, abortPipeline
  }
})