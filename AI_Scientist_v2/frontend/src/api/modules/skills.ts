import client from '../client'

export interface SkillInfo {
  id: string
  name: string
  icon: string
  description: string
  input_schema?: Record<string, string>
  is_custom?: boolean
  type?: string
  prompt_template?: string
  webhook_url?: string
  linked_doc_ids?: number[]
}

export interface SkillRunResult {
  skill_id: string
  skill_name: string
  status: 'success' | 'error'
  result: Record<string, any>
}

export const skillsApi = {
  /** 获取可用技能列表 */
  list: () => client.get<{ skills: SkillInfo[] }>('/skills'),

  /** 创建自定义技能 */
  create: (data: {
    name: string
    description?: string
    prompt_template?: string
    icon?: string
    category?: string
    is_public?: boolean
    webhook_url?: string
    webhook_method?: string
    linked_doc_ids?: number[]
  }) => client.post<{ id: string; name: string; status: string }>('/skills', data),

  /** 执行技能 */
  run: (skillId: string, inputData: Record<string, any>, projectId?: number) =>
    client.post<SkillRunResult>('/skills/run', {
      skill_id: skillId,
      input_data: inputData,
      project_id: projectId,
    }),

  /** 删除自定义技能 */
  delete: (skillId: string) => client.delete(`/skills/${skillId}`),
}