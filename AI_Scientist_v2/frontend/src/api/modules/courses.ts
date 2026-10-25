import client from '../client'
import { useAuthStore } from '@/stores/auth'

// ═══════ 类型 ═══════

export interface Chapter { title: string; points?: string[] }

export interface Course {
  id: number
  title: string
  code: string
  description: string
  syllabus: string
  chapters: Chapter[]
  domain: string
  status: 'draft' | 'published' | 'archived'
  visibility: string
  cover_emoji: string
  enroll_count: number
  view_count: number
  teacher_id: number
  teacher_name: string
  teacher_institution: string
  project_id: number | null
  courseware_count: number
  created_at: string
  is_enrolled?: boolean
  is_teacher?: boolean
  coursewares?: CoursewareBrief[]
  enrollment?: { progress: number; last_courseware_id: number | null; last_slide_index: number } | null
}

export interface CoursewareBrief {
  id: number
  title: string
  source_type: 'upload' | 'ai_generated'
  slide_count: number
  status: string
  version: number
  parent_id: number | null
  file_size: number
  read_size_kb: number
  doc_id: number | null
  staleness: Record<string, any>
  error_message: string
  created_at: string
}

export interface Bullet { level: number; text: string }

export interface SlideMeta {
  slide_index: number
  title: string
  bullets: Bullet[]
  notes: string
  tables: string[][]
  has_image: boolean
  image_kb: number
  risk_score: number
  risk_category: string
  ai_reason: string
  ai_suggestion: string
  updated_by_ai: boolean
}

export interface CoursewareDetail {
  id: number
  title: string
  course_id: number
  course_title: string
  cover_emoji: string
  domain: string
  course_project_id: number | null
  version: number
  parent_id: number | null
  source_type: string
  status: string
  slide_count: number
  file_size: number
  read_size_kb: number
  doc_id: number | null
  is_teacher: boolean
  enrolled: boolean
  staleness: Record<string, any>
  optimization: {
    original_kb?: number; ebook_kb?: number; text_kb?: number; image_kb?: number
    first_paint_kb?: number; saved_percent?: number; full_load_saved_percent?: number
  }
  resume: { courseware_id: number; slide_index: number } | null
  slides: SlideMeta[]
}

export interface MaterialSources {
  documents: { id: number; label: string; ext: string; has_content: boolean }[]
  questions: { question_id: number; label: string; category: string }[]
  tasks: { id: number; label: string; question_id: number }[]
  projects: { id: number; label: string; has_chat: boolean }[]
  pipelines: { id: string; label: string; steps: number }[]
  pipeline_runs: { id: string; pipeline_id: string; status: string; label: string }[]
  skills: { id: string; label: string; type: string }[]
}

/** 多源素材：让 AI 生成/更新课件时能引用原资料、科学问题、报告、项目、对话、流水线、技能 */
export interface MaterialSelection {
  doc_ids?: number[]
  question_ids?: number[]
  task_ids?: number[]
  project_id?: number | null
  chat_project_id?: number | null
  pipeline_run_id?: string | null
  pipeline_run_ids?: string[]
  skill_runs?: { skill_id: string; input_data?: Record<string, any> }[]
}

export interface StalenessItem {
  slide_index: number
  risk_score: number
  category?: string
  reason?: string
  suggestion?: string
}

// ═══════ API ═══════

/** 上传进度回调挂载点（供 CourseDetail 订阅） */
export const uploadProgress: { cb: ((pct: number) => void) | null } = { cb: null }

export const courseApi = {
  list: (params?: { q?: string; domain?: string; scope?: string; limit?: number; offset?: number }) =>
    client.get<{ items: Course[]; total: number; can_teach: boolean }>('/courses', { params }),

  stats: () => client.get<{
    published: number; my_courses: number; my_enrollments: number; total_slides: number
    need_update_coursewares: number; ai_generated_coursewares: number; can_teach: boolean
  }>('/courses/stats'),

  detail: (id: number) => client.get<Course>(`/courses/${id}`),

  create: (data: Partial<Course>) => client.post<Course>('/courses', data),

  update: (id: number, data: Partial<Course> & { status?: string }) =>
    client.patch<Course>(`/courses/${id}`, data),

  remove: (id: number) => client.delete(`/courses/${id}`),

  enroll: (id: number) => client.post(`/courses/${id}/enroll`),
  unenroll: (id: number) => client.delete(`/courses/${id}/enroll`),
  students: (id: number) => client.get<{ items: any[]; total: number }>(`/courses/${id}/students`),

  materials: (limit = 40) =>
    client.get<MaterialSources>('/courses/materials', { params: { limit_per: limit } }),

  /** 上传 PPT → 后端电子化拆解（文本层 + 逐页瘦身图） */
  uploadCourseware: (courseId: number, file: File, title?: string) => {
    const fd = new FormData()
    fd.append('file', file)
    if (title) fd.append('title', title)
    return client.post<CoursewareBrief & { optimization: any }>(`/courses/${courseId}/courseware`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000,
      onUploadProgress: (e) => {
        if (uploadProgress.cb && e.total) uploadProgress.cb(Math.min(90, Math.round((e.loaded / e.total) * 90)))
      },
    })
  },

  generateDeck: (courseId: number, data: {
    topic: string; syllabus?: string; chapter_count?: number; slides_per_chapter?: number
    style?: string; audience?: string; domain?: string; title?: string
    sources?: MaterialSelection; auto_save?: boolean
  }) => client.post<{
    ok: boolean; saved: boolean; courseware_id?: number; slide_count?: number
    chapters?: Chapter[]; cost?: number; title?: string; slides?: SlideMeta[]
    sources_used?: { kind: string; label: string; chars: number }[]
  }>(`/courses/${courseId}/generate-courseware`, data, { timeout: 300000 }),

  syncFromPipeline: (courseId: number, data: {
    pipeline_id: string; run_id?: string | null; topic?: string; chapter_count?: number
    slides_per_chapter?: number; skill_runs?: { skill_id: string }[]; title?: string
  }) => client.post<any>(`/courses/${courseId}/sync-from-pipeline`, data, { timeout: 300000 }),

  aiOutline: (data: { text: string; domain?: string; sources?: MaterialSelection }) =>
    client.post<{ ok: boolean; title: string; domain: string; chapters: Chapter[] }>(
      '/courses/ai/outline', data, { timeout: 240000 }),
}

export const coursewareApi = {
  detail: (id: number) => client.get<CoursewareDetail>(`/coursewares/${id}`),

  /** 图片 URL：用 query token 让 <img> 原生懒加载可用 */
  imageUrl: (id: number, slideIndex: number) => {
    const auth = useAuthStore()
    const t = auth.token ? encodeURIComponent(auth.token) : ''
    return `/api/v1/coursewares/${id}/slides/${slideIndex}/image${t ? `?token=${t}` : ''}`
  },

  ebookUrl: (id: number) => `/api/v1/coursewares/${id}/ebook`,
  exportUrl: (id: number) => `/api/v1/coursewares/${id}/export/pptx`,

  reportProgress: (id: number, slideIndex: number, completed = false) =>
    client.post(`/coursewares/${id}/progress`, { courseware_id: id, slide_index: slideIndex, completed }),

  stalenessScan: (id: number) => client.post<{
    ok: boolean; summary: Record<string, any>; items: StalenessItem[]; cost: number
  }>(`/coursewares/${id}/staleness-scan`, null, { timeout: 300000 }),

  aiRefresh: (id: number, data: { slide_indexes?: number[]; extra_context?: string; sources?: MaterialSelection; title?: string }) =>
    client.post<{
      ok: boolean; updated: number; new_courseware_id: number | null
      version?: number; cost?: number; message?: string; slide_count?: number
      sources_used?: { kind: string; label: string; chars: number }[]
    }>(`/coursewares/${id}/ai-refresh`, data, { timeout: 600000 }),

  versions: (id: number) =>
    client.get<{ items: { id: number; title: string; version: number; source_type: string; slide_count: number; parent_id: number | null; is_current: boolean; created_at: string }[] }>(
      `/coursewares/${id}/versions`),

  editSlides: (id: number, data: { title?: string; slides?: { slide_index: number; title?: string; bullets?: Bullet[]; notes?: string }[] }) =>
    client.patch(`/coursewares/${id}/slides`, data),

  remove: (id: number) => client.delete(`/coursewares/${id}`),
}
