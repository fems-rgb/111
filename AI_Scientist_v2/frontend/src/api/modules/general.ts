import client from '../client'
import { useAuthStore } from '@/stores/auth'

// ═══════ 类型 ═══════

/** 图解块（前端矢量渲染，不依赖文生图） */
export type FigureBlock =
  | { kind: 'flow'; title: string; steps: { label: string; desc: string }[] }
  | { kind: 'compare'; title: string; left: { title: string; items: string[] }; right: { title: string; items: string[] } }
  | { kind: 'cards'; title: string; cards: { icon: string; title: string; desc: string }[] }
  | { kind: 'callout'; tone: 'tip' | 'aha' | 'warn'; title: string; text: string }


/** 课程卡片（课程广场用，不含正文，避免一次拉全部内容） */
export interface GeneralCourseBrief {
  id: number
  title: string
  subtitle: string
  emoji: string
  category: string
  level: string
  summary: string
  tags: string[]
  status: 'draft' | 'published'
  cover_image: string
  lesson_count: number
  ready_count: number
  done_count: number
  minutes_total: number
  created_at: string
}

export interface GeneralLessonBrief {
  id: number
  course_id: number
  order_index: number
  title: string
  kicker: string
  summary: string
  minutes: number
  status: 'pending' | 'ready'
  done: boolean
}

export interface GeneralCourseDetail extends GeneralCourseBrief {
  lessons: GeneralLessonBrief[]
  next_lesson_id: number | null
  is_owner: boolean
  can_edit: boolean
}

export interface GeneralQuizItem {
  q: string
  options: string[]
  answer: number
  explain: string
}

export interface GeneralLessonDetail {
  id: number
  course_id: number
  course_title: string
  title: string
  kicker: string
  summary: string
  content: string
  quiz: GeneralQuizItem[]
  figure: FigureBlock[]
  cover_image: string
  minutes: number
  status: 'pending' | 'ready'
  done: boolean
  prev_id: number | null
  next_id: number | null
  total: number
  index: number
}

export interface GeneralProgressResult {
  ok: boolean
  status: 'learning' | 'done'
  done_count: number
  ready_count: number
  course_percent: number
}

/** 起草结果：只出大纲与章节骨架，正文需要逐节生成 */
export interface GeneralDraftResult {
  ok: boolean
  course_id: number
  title: string
  lesson_count: number
  model: string
}

export interface GeneralGenerateResult {
  ok: boolean
  lesson_id: number
  chars: number
  quiz_count: number
  figure_count: number
  status: string
  model: string
  fallback_from: string | null
}

// ═══════ API ═══════

export const generalApi = {
  /** 课程广场。mine=true 只看自己建的（含草稿） */
  list: (params?: { q?: string; category?: string; level?: string; mine?: boolean }) =>
    client.get<{ items: GeneralCourseBrief[]; categories: { name: string; count: number }[]; can_create: boolean }>(
      '/general/courses', { params }),

  detail: (id: number) => client.get<GeneralCourseDetail>(`/general/courses/${id}`),

  lesson: (id: number) => client.get<GeneralLessonDetail>(`/general/lessons/${id}`),

  /** 上报进度：percent 0-100，或 done=true 直接标记完成 */
  progress: (lessonId: number, data: { percent?: number; done?: boolean }) =>
    client.post<GeneralProgressResult>(`/general/lessons/${lessonId}/progress`, data),

  /** AI 助教：只依据本节内容回答 */
  ask: (lessonId: number, question: string) =>
    client.post<{ ok: boolean; answer: string; model: string }>(
      `/general/lessons/${lessonId}/ask`, { question }, { timeout: 180000 }),

  /** AI 起草一门课：只出大纲，正文逐节生成 */
  draft: (data: { topic: string; audience?: string; level?: string; chapter_count?: number }) =>
    client.post<GeneralDraftResult>('/general/courses/draft', data, { timeout: 240000 }),

  /** 生成单节正文 + 自测题（约 10-20s，失败可单独重试） */
  generateLesson: (lessonId: number, data?: { audience?: string; style?: string; extra?: string }) =>
    client.post<GeneralGenerateResult>(`/general/lessons/${lessonId}/generate`, data || {}, { timeout: 300000 }),

  publish: (id: number) =>
    client.post<{ ok: boolean; status: string; ready_count: number }>(`/general/courses/${id}/publish`),

  remove: (id: number) => client.delete(`/general/courses/${id}`),
}

/**
 * 封面插画 URL。<img> 不会带 Authorization 头，所以用 ?token= 查询认证，
 * 与课件逐页图片、下载链接保持同一套做法。cover 为后端 generated/general 下的文件名。
 */
export function generalCoverUrl(cover: string): string {
  if (!cover) return ''
  const auth = useAuthStore()
  const t = auth.token ? encodeURIComponent(auth.token) : ''
  return `/api/v1/general/media/${encodeURIComponent(cover)}${t ? `?token=${t}` : ''}`
}
