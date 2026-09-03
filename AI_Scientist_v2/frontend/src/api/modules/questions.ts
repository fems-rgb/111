import client from '../client'

export interface QuestionItem {
  question_id: number
  title: string
  title_en?: string
  category: string
  description?: string
  keywords: string[]
  difficulty: string
  source?: string
}

export interface QuestionDetail extends QuestionItem {
  created_at?: string
  task_history: Array<{
    task_id: number
    status: string
  progress?: number
    version: number
    document_path?: string
    created_at?: string
    completed_at?: string
  }>
}

export interface QuestionListResponse {
  total: number
  page: number
  page_size: number
  items: QuestionItem[]
}

export interface CategoryStat {
  category: string
  count: number
}

export interface TaskStatus {
  task_id: number
  question_id: number
  question_title?: string
  status: string
  progress?: number
  result?: Record<string, any>
  document_path?: string
  version: number
  feedback?: string
  error_message?: string
  created_at?: string
  completed_at?: string
}

export interface MyTaskItem {
  task_id: number
  question_id: number
  question_title?: string
  status: string
  progress?: number
  version: number
  document_path?: string
  created_at?: string
  completed_at?: string
}

export interface DocumentContent {
  task_id: number
  content: string
  source: string
  path?: string
}

// 鑾峰彇棰樼洰鍒楄〃
export function getQuestions(params: {
  category?: string
  keyword?: string
  difficulty?: string
  page?: number
  page_size?: number
}) {
  return client.get<QuestionListResponse>('/questions/', { params })
}

// 鑾峰彇鍗曚釜棰樼洰璇︽儏
export function getQuestionDetail(questionId: number) {
  return client.get<QuestionDetail>(`/questions/${questionId}`)
}

// 鑾峰彇鍒嗙被缁熻
export function getCategories() {
  return client.get<CategoryStat[]>('/questions/categories')
}

// 鐢ㄦ埛鑷富娣诲姞棰樼洰
export function createQuestion(data: {
  title: string
  title_en?: string
  category: string
  description?: string
  keywords?: string[]
  difficulty?: string
}) {
  return client.post<{ message: string; question_id: number; title: string }>(
    '/questions/create', data
  )
}

// 鎻愪氦鐢熸垚浠诲姟锛堟敮鎸佺洿鎺ョ敓鎴愭垨娴佹按绾匡級
export function generateQuestionDoc(
  questionId: number,
  customPrompt = '',
  pipelineId?: string
) {
  return client.post<{ task_id: number; status: string; message: string }>(
    '/questions/generate',
    { question_id: questionId, custom_prompt: customPrompt, pipeline_id: pipelineId || undefined }
  )
}

// 鎵归噺鐢熸垚
export function batchGenerateDocs(
  questionIds: number[],
  customPrompt = '',
  pipelineId?: string
) {
  return client.post<{
    message: string
    tasks: Array<{ question_id: number; task_id: number }>
    errors: Array<{ question_id: number; error: string }>
    total_submitted: number
  }>('/questions/batch-generate', {
    question_ids: questionIds,
    custom_prompt: customPrompt,
    pipeline_id: pipelineId || undefined,
  })
}

// 鏌ヨ浠诲姟鐘舵€?
export function getTaskStatus(taskId: number) {
  return client.get<TaskStatus>(`/questions/tasks/${taskId}`)
}

// 璇诲彇鏂囨。鍐呭
export function getTaskDocument(taskId: number) {
  return client.get<DocumentContent>(`/questions/tasks/${taskId}/document`)
}

// 鎻愪氦鍙嶉
export function submitFeedback(taskId: number, feedback: string) {
  return client.post<{ message: string; task_id: number }>(
    '/questions/feedback',
    { task_id: taskId, feedback }
  )
}

// 鎴戠殑浠诲姟鍘嗗彶
export function getMyTasks(params: { page?: number; page_size?: number; status?: string }) {
  return client.get<{ total: number; page: number; page_size: number; items: MyTaskItem[] }>(
    '/questions/my-tasks',
    { params }
  )
}

// 鍒犻櫎鍗曚釜浠诲姟
export function deleteTask(taskId: number) {
  return client.delete<{ message: string; task_id: number }>(`/questions/tasks/${taskId}`)
}

// 鎵归噺鍒犻櫎浠诲姟
export function batchDeleteTasks(taskIds: number[]) {
  return client.post<{ message: string; deleted: number; errors: any[] }>(
    '/questions/tasks/batch-delete',
    { task_ids: taskIds }
  )
}


// 批量导入题目
export function batchImportQuestions(questions: any[], skipExisting = true) {
  return client.post<{ message: string; imported: number; skipped: number; errors: any[] }>(
    '/questions/batch-import',
    { questions, skip_existing: skipExisting }
  )
}

// 重试失败任务
export function retryTask(taskId: number, customPrompt = '') {
  return client.post<{
    task_id: number
    status: string
    message: string
    retried_from: number
    version: number
    }>(`/questions/tasks/${taskId}/retry`, { custom_prompt: customPrompt })
}

export function batchDeleteQuestions(questionIds: number[]) {
  return client.post<{ message: string; deleted: number }>(
    '/questions/batch-delete',
    { question_ids: questionIds }
  )
}

export function deleteAllQuestions() {
  return client.delete<{ message: string; deleted: number }>(
    '/questions/delete-all'
  )
}
