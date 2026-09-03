import client from '../client'

export interface PipelineStep {
  agent_name?: string
  name?: string
  params?: string
  research_question?: string
  model?: string
  [key: string]: any
}

export interface Pipeline {
  id: string
  name: string
  description: string
  steps: PipelineStep[]
  trigger: 'manual' | 'scheduled' | 'webhook'
  schedule_cron?: string
  status: 'idle' | 'running' | 'failed'
  last_run: string | null
  run_count: number
  created_at: string
}

export interface StepLog {
  step: number
  agent: string
  status: 'running' | 'completed' | 'failed' | 'cancelled'
  started_at?: string
  duration_ms?: number
  result_summary?: string
  error?: string
  tokens?: number
  cost_yuan?: number
}

export interface PipelineLog {
  run_id: string
  pipeline_id?: string
  started_at: string
  finished_at?: string
  status: 'running' | 'completed' | 'failed' | 'cancelled'
  steps: StepLog[]
}

export interface ParamField {
  key: string
  label: string
  type: "text" | "textarea" | "select"
  placeholder?: string
  default?: string
  required?: boolean
  options?: { value: string; label: string }[]
}

export interface PipelineTemplate {
  id: string
  name: string
  description: string
  icon: string
  steps: PipelineStep[]
  trigger: string
  params_schema?: ParamField[]
}

export const automationApi = {
  /** 获取流水线列表 */
  list: () => client.get<{ pipelines: Pipeline[] }>('/automation'),

  /** 创建流水线 */
  create: (data: { name: string; description?: string; steps?: any[]; trigger?: string; schedule_cron?: string; template_id?: string }) =>
    client.post<Pipeline>('/automation', data),

  /** 获取单个流水线详情 */
  get: (id: string) => client.get<Pipeline>(`/automation/${id}`),

  /** 触发执行 */
  run: (id: string) => client.post<{ message: string; run_id: string; log: PipelineLog }>(`/automation/${id}/run`),

  /** 停止执行 */
  stop: (id: string) => client.post<{ message: string }>(`/automation/${id}/stop`),

  /** 获取执行日志 */
  logs: (id: string) => client.get<{ logs: PipelineLog[] }>(`/automation/${id}/logs`),

  /** 更新流水线 */
  update: (id: string, data: { name?: string; description?: string; steps?: any[]; trigger?: string; schedule_cron?: string }) =>
    client.put<Pipeline>(`/automation/${id}`, data),

  /** 删除流水线 */
  delete: (id: string) => client.delete(`/automation/${id}`),

  /** 获取预设模板 */
  templates: () => client.get<{ templates: PipelineTemplate[] }>('/automation/templates'),

  fromTemplate: (templateId: string, params?: Record<string, string>) =>
    client.post<Pipeline>(`/automation/from-template/${templateId}`, params ? { params } : {}),
}
