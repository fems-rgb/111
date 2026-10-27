import client from '../client'

export type PlanScope = 'personal' | 'team' | 'pipeline' | 'auto'
export type PlanSource = 'manual' | 'ai'
export type PlanStatus = 'active' | 'done' | 'cancelled'

export interface PlanItem {
  text: string
  due?: string
  agent?: string
  done?: boolean
}

export interface Plan {
  id: number
  owner_id: number
  scope: PlanScope
  project_id: number | null
  project_title?: string
  title: string
  items: PlanItem[]
  source: PlanSource
  status: PlanStatus
  due_at: string | null
  pipeline_id: string
  created_at: string
  updated_at: string
}

export const plansApi = {
  list: (scope?: PlanScope) =>
    client.get<{ ok: boolean; items: Plan[] }>('/plans', { params: scope ? { scope } : {}, timeout: 15000 }),
  create: (payload: { title: string; scope: PlanScope; project_id?: number | null; items?: PlanItem[]; due_at?: string | null }) =>
    client.post<{ ok: boolean; plan: Plan }>('/plans', payload, { timeout: 15000 }),
  update: (id: number, payload: Partial<{ title: string; items: PlanItem[]; status: PlanStatus; due_at: string | null; project_id: number | null }>) =>
    client.patch<{ ok: boolean; plan: Plan }>(`/plans/${id}`, payload, { timeout: 15000 }),
  remove: (id: number) => client.delete<{ ok: boolean }>(`/plans/${id}`, { timeout: 15000 }),
  ai: (payload: { topic: string; scope: PlanScope; project_id?: number | null; mode?: string; model?: string }) =>
    client.post<{ ok: boolean; plan: Plan; model_used: string }>('/plans/ai', payload, { timeout: 90000 }),
  toPipeline: (id: number) =>
    client.post<{ ok: boolean; pipeline_id: string; steps_count: number; plan: Plan; run_hint: string }>(
      `/plans/${id}/to-pipeline`, {}, { timeout: 20000 }),
}
