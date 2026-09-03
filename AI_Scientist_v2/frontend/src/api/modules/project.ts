import client from '../client'
import type { Project, ProjectStats, AgentTask } from '@/types'

export const projectApi = {
  list: (params?: { status?: string; workspace?: string; limit?: number; offset?: number }) =>
    client.get<Project[]>('/projects', { params }),
  get: (id: number) => client.get<Project>(`/projects/${id}`),
  create: (data: { title: string; description?: string; research_question: string; domain?: string; tags?: string[]; workspace?: string; hypothesis?: string; verification_method?: string; visibility?: string; evidence_files?: string[] }) =>
    client.post<Project>('/projects', data),
  update: (id: number, data: Partial<Project>) => client.patch(`/projects/${id}`, data),
  delete: (id: number) => client.delete(`/projects/${id}`),
  start: (id: number, pipeline?: string[]) => pipeline ? client.post(`/projects/${id}/start`, { pipeline }) : client.post(`/projects/${id}/start`),
  pause: (id: number) => client.post(`/projects/${id}/pause`),
  resume: (id: number) => client.post(`/projects/${id}/resume`),
  restart: (id: number, pipeline?: string[]) => pipeline ? client.post(`/projects/${id}/restart`, { pipeline }) : client.post(`/projects/${id}/restart`),
  getTasks: (id: number) => client.get<AgentTask[]>(`/projects/${id}/tasks`),
  getStats: (params?: { workspace?: string }) => client.get<ProjectStats>('/projects/stats', { params }),
  share: (id: number, target_workspace: string) => client.post(`/projects/${id}/share`, { target_workspace }),
  unshare: (id: number, target_workspace: string) => client.delete(`/projects/${id}/share/${target_workspace}`),
}
