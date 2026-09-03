import client from '../client'

export interface KnowledgeDoc {
  id: number
  title: string
  doc_type: string
  file_size: number
  chunk_count: number
  status: string
  created_at: string
}

export interface ExternalPaper {
  title: string
  authors: string[]
  year: number | null
  abstract: string
  citations: number
  url: string
  pdf_url: string | null
  source: string
  external_id: string
}

export interface SearchResult {
  total: number
  papers: ExternalPaper[]
  source_counts: Record<string, number>
  hint?: string
}

export const knowledgeApi = {
  // 获取文档列表
  listDocs: async (params?: { status?: string; search?: string; limit?: number; offset?: number }) => {
    const res = await client.get('/knowledge', {
      params: { q: params?.search || '', limit: params?.limit || 100, offset: params?.offset || 0 }
    })
    const items = (res.data.items || []).map((d: any) => ({
      id: d.id,
      title: d.filename || '未命名',
      doc_type: d.file_ext || 'unknown',
      file_size: d.file_size || 0,
      chunk_count: d.chunk_count || 0,
      status: d.parse_status || 'pending',
      created_at: d.created_at || ''
    }))
    return { data: items, total: res.data.total || 0 }
  },

  // 上传文档
  uploadDoc: (file: File, metadata?: Record<string, string>) => {
    const formData = new FormData()
    formData.append('file', file)
    if (metadata) formData.append('description', JSON.stringify(metadata))
    return client.post('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    })
  },

  getFile: (id: number) => client.get(`/knowledge/${id}/file`, { responseType: 'blob' }),
  deleteDoc: (id: number) => client.delete(`/knowledge/${id}`),
  reindexDoc: (id: number) => client.post('/knowledge/reindex'),
  reindexAll: () => client.post('/knowledge/reindex'),
  getDocContent: (id: number) => client.get(`/knowledge/documents/${id}/preview`),

  getStats: async () => {
    const res = await client.get('/knowledge/stats')
    const d = res.data
    return {
      data: {
        total_docs: d.total || 0,
        indexed: Object.values(d.by_ext || {}).reduce((a: number, b: any) => a + b, 0),
        processing: 0,
        total_size: d.total_size_bytes || 0
      }
    }
  },

  // ===== 外部资料采集 =====
  searchExternal: (params: { q: string; sources?: string; limit?: number; year_from?: number }) =>
    client.get<SearchResult>('/knowledge/external/search', { params }),

  fetchUrl: (url: string) =>
    client.post('/knowledge/external/fetch-url', { url }),

  fetchUrlsBatch: (urls: string[]) =>
    client.post('/knowledge/external/fetch-urls-batch', { urls }),

  importPaper: (paper: ExternalPaper, savePath?: string) =>
    client.post('/knowledge/external/import', { paper, save_path: savePath }),

  importPapersBatch: (papers: ExternalPaper[]) =>
    client.post('/knowledge/external/import-batch', { papers }),

  // ===== 本地知识库 RAG 搜索 =====
  searchKnowledge: (params: { q: string; limit?: number }) =>
    client.get<{results: any[]; total: number; query: string}>('/knowledge/search', { params }),
}
