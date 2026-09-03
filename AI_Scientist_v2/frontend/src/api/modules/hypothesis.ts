import request from '../client'

export interface Hypothesis {
  id: number
  hypo_id: string
  statement: string
  variables: any[]
  testability_score: number
  suggested_method: string
  evidence_chain: string
  version: number
  parent_id: number | null
  status: string
  created_at: string
  novelty_score?: number | null
  feasibility_score?: number | null
  impact_score?: number | null
  overall_score?: number | null
  ai_reasoning?: string | null
  literature_refs?: any[]
  rejected_reason?: string | null
  falsifiability_score?: number | null
  evidence_consistency?: number | null
  counter_evidence?: string | null
}


export interface IterationRecord {
  iteration_num: number
  feedback: string
  experiment_result: string
  score_before: number
  score_after: number
  created_at: string | null
}

export function getHypotheses(projectId: number) {
  return request.get<Hypothesis[]>(`/projects/${projectId}/hypotheses`)
}

export function getIterations(projectId: number) {
  return request.get<IterationRecord[]>(`/projects/${projectId}/iterations`)
}

export function submitFeedback(projectId: number, data: {
  feedback: string
  experiment_result?: string
  iteration_num?: number
}) {
  return request.post(`/projects/${projectId}/feedback`, data)
}
