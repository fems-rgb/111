import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AgentInfo } from '@/types'
import { agentApi } from '@/api/modules/agent'

export const useAgentStore = defineStore('agent', () => {
  const agents = ref<AgentInfo[]>([])

  async function fetchAgents() {
    const res = await agentApi.list()
    agents.value = res.data
  }

  async function reviewTask(taskId: number, approved: boolean, comment: string) {
    return await agentApi.review(taskId, approved, comment)
  }

  async function directChat(message: string, agentName = 'general', model = 'qwen-plus') {
    return await agentApi.directChat(message, agentName, model)
  }

  return { agents, fetchAgents, reviewTask, directChat }
})