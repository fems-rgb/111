import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

// 全局应用状态：主题/侧栏/模式 + 题库视图持久化 + 生成进度跨路由小窗
//
// 生成进度小窗（AppLayout.vue 消费）：
//   - genTaskId / genStatus / genProgress / genTitle / genMinimized
//   - startGenTracking(taskId, title)：任务提交后立即初始化
//   - updateGenProgress({status, progress, title})：轮询回写
//   - closeGenProgress()：完成/失败/用户关闭 → 清空

export const useAppStore = defineStore('app', () => {
  // ===== 基础 UI 状态 =====
  const sidebarCollapsed = ref(false)
  const darkMode = ref(localStorage.getItem('ai_dark_mode') === 'true')
  const mode = ref<'quick' | 'expert'>((localStorage.getItem('ai_mode') as any) || 'quick')
  const currentWorkspace = ref(localStorage.getItem('ai_workspace') || 'personal')
  // 全局首选模型：'' = 按模式自动定档；顶栏 ModelSwitcher 与各请求层共用
  const preferredModel = ref(localStorage.getItem('ai_pref_model') || '')

  function applyDarkMode(val: boolean) {
    if (val) document.documentElement.classList.add('dark')
    else document.documentElement.classList.remove('dark')
  }
  applyDarkMode(darkMode.value)
  watch(darkMode, (val) => {
    localStorage.setItem('ai_dark_mode', String(val))
    applyDarkMode(val)
  })
  watch(mode, (val) => localStorage.setItem('ai_mode', val))
  watch(currentWorkspace, (val) => localStorage.setItem('ai_workspace', val))
  watch(preferredModel, (val) => localStorage.setItem('ai_pref_model', val))

  // ===== 题库视图持久化状态（跨路由切换不丢失） =====
  // 内部字段用宽松类型，消费端 (QuestionsView) 通过带类型的 computed 消费
  const questionsView = ref<{
    activeTab: 'questions' | 'tasks' | string
    detailData: any | null
    showGenDialog: boolean
    genTarget: any | null
    genMode: 'pipeline' | 'direct' | string
  }>({
    activeTab: (localStorage.getItem('ai_qbank_tab') as any) || 'questions',
    detailData: (() => { try { return JSON.parse(localStorage.getItem('ai_qbank_detail') || 'null') } catch { return null } })(),
    showGenDialog: false,
    genTarget: null,
    genMode: (localStorage.getItem('ai_qbank_genmode') as any) || 'pipeline',
  })
  watch(() => questionsView.value.activeTab, (val) => localStorage.setItem('ai_qbank_tab', val))
  watch(() => questionsView.value.detailData, (val) => {
    try { localStorage.setItem('ai_qbank_detail', JSON.stringify(val)) } catch { /* quota / circular */ }
  }, { deep: true })
  watch(() => questionsView.value.genMode, (val) => localStorage.setItem('ai_qbank_genmode', val))

  // ===== Toast =====
  const toastMsg = ref('')
  const toastType = ref<'success' | 'error' | 'info' | 'warning'>('info')
  function showToast(msg: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') {
    toastMsg.value = msg
    toastType.value = type
    setTimeout(() => { toastMsg.value = '' }, 3000)
    // 全局只渲染 toasts 数组（AppLayout），单写 toastMsg 是看不到任何提示的
    showToastMulti(msg, type)
  }
  const toasts = ref<Array<{ id: number; message: string; type: 'success' | 'error' | 'info' | 'warning' }>>([])
  let toastId = 0
  function showToastMulti(msg: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') {
    const id = ++toastId
    toasts.value.push({ id, message: msg, type })
    setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, 3000)
  }

  // ===== 生成进度（跨路由小窗）=====
  type GenStatus = 'pending' | 'running' | 'completed' | 'failed' | string
  const genTaskId = ref<number | null>(null)
  const genStatus = ref<GenStatus>('')
  const genProgress = ref(0)
  const genTitle = ref('')
  const genMinimized = ref(false)

  function startGenTracking(taskId: number, title: string) {
    genTaskId.value = taskId
    genTitle.value = title || ''
    genStatus.value = 'running'
    genProgress.value = 0
    genMinimized.value = false
  }
  function updateGenProgress(payload: { status?: GenStatus; progress?: number; title?: string }) {
    if (payload.status !== undefined) genStatus.value = payload.status
    if (payload.progress !== undefined) genProgress.value = payload.progress
    if (payload.title !== undefined) genTitle.value = payload.title
  }
  function closeGenProgress() {
    // 关闭 = 清空所有跟踪字段，让 AppLayout 小窗隐藏
    genTaskId.value = null
    genStatus.value = ''
    genProgress.value = 0
    genTitle.value = ''
    genMinimized.value = false
  }
  function toggleGenMinimized() { genMinimized.value = !genMinimized.value }

  // ===== 基础动作 =====
  function toggleSidebar() { sidebarCollapsed.value = !sidebarCollapsed.value }
  function toggleDarkMode() { darkMode.value = !darkMode.value }
  function setMode(m: 'quick' | 'expert') { mode.value = m }
  function setWorkspace(ws: string) { currentWorkspace.value = ws }
  function setPreferredModel(m: string) { preferredModel.value = m }

  return {
    // UI
    sidebarCollapsed, darkMode, mode, currentWorkspace, preferredModel,
    toggleSidebar, toggleDarkMode, setMode, setWorkspace, setPreferredModel,
    // 题库视图
    questionsView,
    // Toast
    toastMsg, toastType, toasts, showToast, showToastMulti,
    // 生成进度小窗
    genTaskId, genStatus, genProgress, genTitle, genMinimized,
    startGenTracking, updateGenProgress, closeGenProgress, toggleGenMinimized,
  }
})
