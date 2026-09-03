import client from '../client'
import type { AgentInfo } from '@/types'

export const agentApi = {
  list: () => client.get<AgentInfo[]>('/agents'),
  review: (taskId: number, approved: boolean, comment: string) =>
    client.post(`/agents/tasks/${taskId}/review`, { approved, comment }),
  directChat: (message: string, agentName = 'general', model = 'qwen-plus') =>
    client.post('/agents/chat', { message, agent_name: agentName, model }),
}