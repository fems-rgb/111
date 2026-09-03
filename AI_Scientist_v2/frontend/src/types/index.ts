export interface User {
  id: number
  username: string
  email: string
  display_name: string
  role: string
  avatar_url: string
  institution: string
  bio: string
  created_at: string
  is_active?: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface Project {
  id: number
  title: string
  description: string
  research_question: string
  domain: string
  status: string
  complexity: string | null
  final_output: string
  review_score: number | null
  tags: string[]
  created_at: string
  updated_at: string
  hypothesis_count?: number
  closure_stage?: number
  hypothesis?: string
  verification_method?: string
  visibility?: string
  evidence_files?: string[]
}

export interface AgentTask {
  id: number
  project_id: number
  agent_name: string
  step_order: number
  status: string
  output_data: string
  error_message: string
  retry_count: number
  requires_review: boolean
  review_comment: string
  tokens_used: number
  cost_yuan: number
  model_used: string
  started_at: string | null
  finished_at: string | null
}

export interface AgentInfo {
  name: string
  display_name: string
  description: string
  requires_review: boolean
}

export interface ChatMessage {
  id: number
  project_id: number | null
  user_id: number
  role: string
  content: string
  content_type: string
  tokens_used: number
  created_at: string
}

export interface TraceRecord {
  span_id: string
  trace_id: string
  parent_span_id: string | null
  span_type: string
  span_name: string
  project_id: number | null
  task_id: number | null
  input_data: string
  output_data: string
  tokens_used: number
  cost_yuan: number
  status: string
  error_detail: string
  duration_ms: number
  created_at: string
}

export interface CostSummary {
  total_cost_yuan: number
  total_tokens: number
  call_count: number
  model_breakdown: Record<string, { cost: number; tokens: number; calls: number }>
}

export interface ProjectStats {
  total: number
  running: number
  completed: number
  task_count?: number
  active_pipelines?: number
  trace_count?: number
}


// ===== 技能市场类型 =====
export interface SkillInfo {
  id: string
  name: string
  icon: string
  description: string
  input_schema?: Record<string, string>
}

export interface SkillRunResult {
  skill_id: string
  skill_name: string
  status: 'success' | 'error'
  result: Record<string, any>
}

// ===== 自动化流水线类型 =====
export interface Pipeline {
  id: string
  name: string
  description: string
  steps: Array<Record<string, any>>
  trigger: 'manual' | 'scheduled' | 'webhook'
  status: 'idle' | 'running' | 'failed'
  last_run: string | null
  run_count: number
  created_at: string
}

export interface PipelineLog {
  run_id: string
  started_at: string
  finished_at?: string
  status: 'running' | 'completed' | 'failed'
  steps: Array<{ step: number; agent: string; status: string; duration_ms: number }>
}
