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

export interface SlideCard { title: string; desc: string }
export interface SlideMetric { value: string; unit: string; label: string }
export interface SlideCompareSide { title: string; items: string[] }
export interface SlideCompare { left: SlideCompareSide; right: SlideCompareSide }

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
  // 版式语义（AI 生成课件才有；上传课件缺失时回退到要点+配图）
  chapter?: string
  layout?: 'cover' | 'section' | 'bullets' | 'cards' | 'compare' | 'metric'
    | 'chart' | 'flow' | 'split' | 'quote' | 'table' | 'end'
  kicker?: string
  lead?: string
  cards?: SlideCard[]
  metrics?: SlideMetric[]
  compare?: SlideCompare
  quote?: string
  quote_by?: string
  takeaway?: string[]
  key_question?: string
  chapter_no?: number
  // 「讲透这一页」与图表/流程（新版生成器产出，旧课件为空）
  detail?: string
  example?: string
  chart?: SlideChart | null
  steps?: SlideStep[]
}

export interface SlideChart {
  type: 'bar' | 'hbar' | 'line'
  labels: string[]
  values: number[]
  unit?: string
  caption?: string
  series_name?: string
}

export interface SlideStep {
  title: string
  desc?: string
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

/** 课件工坊一键生成的返回 */
export interface DeckResult {
  ok: boolean
  saved: boolean
  course_id?: number
  course_title?: string
  courseware_id?: number
  title?: string
  slide_count?: number
  version?: number
  chapters?: Chapter[]
  slides?: SlideMeta[]
  cost?: number
  pptx_url?: string
  ebook_url?: string
  handout_url?: string
  reader_url?: string
  exercises?: string[]
  reading?: string[]
  sources_used?: { kind: string; label: string; chars: number }[]
}

/** 一键生成作业状态（进度可视化的数据源） */
export interface GenerateJobStatus {
  ok: boolean
  job_id: string
  status: 'running' | 'done' | 'failed' | 'cancelled'
  stage: string
  percent: number
  message: string
  chapters_done: number
  chapters_total: number
  slides_done: number
  slides_total: number
  topic?: string
  course_id?: number
  course_title?: string
  result?: DeckResult | null
  error?: string
}

/** 课件生成可选模型（/coursewares/generate-models） */
export interface GenerateModelItem {
  value: string
  label: string
  desc: string
  is_default: boolean
}

/** 工坊历史列表项 */
export interface AiCoursewareItem {
  id: number
  title: string
  course_id: number
  course_title: string
  slide_count: number
  version: number
  status: string
  read_size_kb: number
  created_at: string
  pptx_url: string
  reader_url: string
}

// ═══════ API ═══════

/** 上传进度回调挂载点（供 CourseDetail 订阅） */
export const uploadProgress: { cb: ((pct: number) => void) | null } = { cb: null }

/** 下载类链接由浏览器直接发起（不会带 Authorization 头），所以用 query token 认证 */
function _tokenQuery() {
  const auth = useAuthStore()
  return auth.token ? `?token=${encodeURIComponent(auth.token)}` : ''
}

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

  // 课程内的「AI 生成课件」已统一到 coursewareApi.startGenerate + generateStatus（带真实进度），
  // 不再保留一份同步阻塞的旧接口，避免两套生成行为不一致。

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

  ebookUrl: (id: number) => `/api/v1/coursewares/${id}/ebook${_tokenQuery()}`,
  /** 讲义：学生版留笔记空位，教师版附讲师速记与时长建议 */
  handoutUrl: (id: number, audience: 'student' | 'teacher' = 'student') =>
    `/api/v1/coursewares/${id}/handout${_tokenQuery()}${_tokenQuery() ? '&' : '?'}audience=${audience}`,
  exportUrl: (id: number) => `/api/v1/coursewares/${id}/export/pptx${_tokenQuery()}`,

  /** 课件工坊：起一个生成作业，立即拿 job_id（真实进度靠 generateStatus 轮询） */
  startGenerate: (data: {
    topic: string; title?: string; domain?: string; syllabus?: string
    chapter_count?: number; slides_per_chapter?: number; style?: string; audience?: string
    course_id?: number | null; sources?: MaterialSelection; auto_save?: boolean; model?: string
  }) => client.post<{ ok: boolean; job_id: string; course_id: number; course_title: string; status_url: string }>(
    '/coursewares/quick-generate', data, { timeout: 120000 }),

  /** 轮询生成进度 */
  generateStatus: (jobId: string) =>
    client.get<GenerateJobStatus>(`/coursewares/quick-generate/${jobId}`, { timeout: 30000 }),

  /** 停止一个正在生成的作业（可调控） */
  cancelGenerate: (jobId: string) =>
    client.post<{ ok: boolean; cancelled: boolean }>(`/coursewares/quick-generate/${jobId}/cancel`, null, { timeout: 30000 }),

  /** 可选模型列表 */
  generateModels: () =>
    client.get<{ ok: boolean; default: string; items: GenerateModelItem[] }>('/coursewares/generate-models'),

  /** 我在工坊里生成过的课件 */
  aiMine: (limit = 30) =>
    client.get<{ items: AiCoursewareItem[]; can_teach: boolean }>('/coursewares/ai-mine', { params: { limit } }),

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
