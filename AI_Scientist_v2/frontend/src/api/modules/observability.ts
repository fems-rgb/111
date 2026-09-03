import client from '../client'
import type { TraceRecord, CostSummary } from '@/types'

export const observabilityApi = {
  getTraces: (projectId?: number, limit = 50) =>
    client.get<TraceRecord[]>('/observability/traces', { params: { project_id: projectId, limit } }),
  getTraceDetail: (traceId: string) =>
    client.get<TraceRecord[]>(`/observability/traces/${traceId}`),
  getCost: () => client.get<CostSummary>('/observability/cost'),
}