import client from '../client'

export type GraphScope = 'general' | 'kb' | 'project' | 'syllabus'

export interface GraphNode {
  id: string
  label: string
  group: string
}

export interface GraphEdge {
  0: string
  1: string
  2: string
  length: number
}

export interface GraphPayload {
  ok: boolean
  scope: GraphScope
  scope_id: string
  status: 'ready' | 'empty' | string
  nodes: GraphNode[]
  edges: [string, string, string][]
  model_used: string
  updated_at: string
}

export const graphsApi = {
  get: (scope: GraphScope, scopeId: string | number) =>
    client.get<GraphPayload>(`/graphs/${scope}/${scopeId}`, { timeout: 15000 }),
  rebuild: (scope: GraphScope, scopeId: string | number, payload: { mode?: string; model?: string } = {}) =>
    client.post<GraphPayload>(`/graphs/${scope}/${scopeId}/rebuild`, payload, { timeout: 120000 }),
}
