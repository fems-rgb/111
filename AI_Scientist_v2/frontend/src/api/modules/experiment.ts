import client from '../client'
import { useAuthStore } from '@/stores/auth'

export interface ExperimentStatus {
  run_id: number; status: string; title: string; output_text: string
  charts: Array<{path: string; filename: string}>; video_path: string | null
  data_table: {columns: string[]; rows: string[][]} | null
  error_message: string; duration_ms: number
  created_at?: string; completed_at?: string
}

export interface TemplateInfo {
  id: number; name: string; description: string; category: string; is_builtin: boolean
}

export function runExperiment(data: {code: string; title?: string; project_id?: number; question_task_id?: number; generate_video?: boolean; timeout?: number}) {
  return client.post<{run_id: number; status: string}>('/experiment-lab/run', data)
}
export function getExperimentStatus(id: number) {
  return client.get<ExperimentStatus>(`/experiment-lab/status/${id}`)
}
export function getExperimentHistory(params: {page?: number; page_size?: number; project_id?: number}) {
  return client.get<{total: number; items: any[]}>('/experiment-lab/history', {params})
}
export function getExperimentTemplates() {
  return client.get<{templates: TemplateInfo[]}>('/experiment-lab/templates')
}
export function getTemplateCode(id: number) {
  return client.get<{id: number; name: string; code: string; description: string; category: string}>(`/experiment-lab/templates/${id}`)
}
export function createTemplate(data: {name: string; description: string; code: string; category?: string}) {
  return client.post<{id: number; name: string; message: string}>('/experiment-lab/templates', data)
}
export function updateTemplate(id: number, data: {name?: string; description?: string; code?: string; category?: string}) {
  return client.put<{id: number; message: string}>(`/experiment-lab/templates/${id}`, data)
}
export function deleteTemplate(id: number) {
  return client.delete<{message: string}>(`/experiment-lab/templates/${id}`)
}

/** Get chart URL - uses authenticated API endpoint */
export function getChartUrl(runId: number, filename: string) {
  const token = useAuthStore().token || ''
  return `/api/v1/experiment-lab/chart/${runId}/${filename}?token=${encodeURIComponent(token)}`
}
/** Get video URL - uses authenticated API endpoint */
export function getVideoUrl(runId: number) {
  const token = useAuthStore().token || ''
  return `/api/v1/experiment-lab/video/${runId}?token=${encodeURIComponent(token)}`
}
/** Detect if video path is a video format (mp4/avi/mov/webm) vs gif */
export function isVideoFormat(videoPath: string | null): boolean {
  if (!videoPath) return false
  const ext = videoPath.toLowerCase().split('.').pop() || ''
  return ['mp4', 'avi', 'mov', 'webm'].includes(ext)
}

/** 删除单条实验记录 */
export function deleteExperimentRun(runId: number) {
  return client.delete<{message: string; run_id: number}>(`/experiment-lab/runs/${runId}`)
}

/** 批量删除实验记录 */
export function batchDeleteExperimentRuns(runIds: number[]) {
  return client.post<{message: string; deleted: number; errors: any[]}>('/experiment-lab/runs/batch-delete', { run_ids: runIds })
}
