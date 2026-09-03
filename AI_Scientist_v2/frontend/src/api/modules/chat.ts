import client from '../client'
import type { ChatMessage } from '@/types'

export const chatApi = {
  send: (content: string, projectId?: number) =>
    client.post('/chat/send', { content, project_id: projectId }),
  history: (projectId?: number, limit = 50) =>
    client.get<ChatMessage[]>('/chat/history', { params: { project_id: projectId, limit } }),
  deleteHistory: (projectId?: number) =>
    client.delete('/chat/history', { params: { project_id: projectId } }),
}

// ===== 断点续传 API =====
export const uploadApi = {
  /** 初始化分片上传 */
  init: (filename: string, totalSize: number, contentType?: string) => {
    const formData = new FormData()
    formData.append('filename', filename)
    formData.append('total_size', String(totalSize))
    if (contentType) formData.append('content_type', contentType)
    return client.post('/multimodal/upload/init', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  /** 上传单个分片 */
  uploadChunk: (uploadId: string, chunkIndex: number, chunkHash: string, blob: Blob) => {
    const formData = new FormData()
    formData.append('upload_id', uploadId)
    formData.append('chunk_index', String(chunkIndex))
    formData.append('chunk_hash', chunkHash)
    formData.append('file', blob)
    return client.post('/multimodal/upload/chunk', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000
    })
  },

  /** 完成上传并合并 */
  complete: (uploadId: string, description?: string) => {
    const formData = new FormData()
    formData.append('upload_id', uploadId)
    if (description) formData.append('description', description)
    return client.post('/multimodal/upload/complete', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000
    })
  },

  /** 查询上传进度（断点恢复） */
  getStatus: (uploadId: string) =>
    client.get(`/multimodal/upload/status/${uploadId}`),

  /** 普通小文件直传（<2MB） */
  directUpload: (file: File, description?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (description) formData.append('description', description)
    return client.post('/multimodal/upload-research-file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000
    })
  }
}
