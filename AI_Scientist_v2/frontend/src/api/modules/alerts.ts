import client from '../client'

/** 统一预警中心条目（GET /alerts） */
export interface AlertItem {
  id: string
  type: 'cost_over_threshold' | 'model_rate_limited' | 'provider_key_missing' | 'job_failed' | string
  severity: 'error' | 'warning' | 'info' | string
  title: string
  message: string
  action_label: string
  action_href: string
  created_at: string
}

export const alertsApi = {
  list: () => client.get<{ ok: boolean; alerts: AlertItem[] }>('/alerts', { timeout: 20000 }),
}
