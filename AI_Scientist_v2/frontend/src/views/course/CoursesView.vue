<template>
  <div class="space-y-5 animate-fade-in">
    <!-- 头部 -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold flex items-center gap-2">🎓 课程中心</h1>
        <p class="text-sm text-surface-500 mt-1">
          老师开课 · PPT 电子化阅读 · AI 陈旧度体检与自动更新 · 流水线产出转讲义
        </p>
      </div>
      <div class="flex flex-wrap gap-2" v-if="canTeach">
        <button @click="$router.push('/courseware-studio')"
                class="px-4 py-2 rounded-lg bg-gradient-to-r from-primary-600 to-accent-600 text-white text-sm font-medium hover:opacity-90 transition-opacity">
          📽️ 一键生成 PPT
        </button>
        <button @click="openCreate"
                class="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors">
          ＋ 新建课程
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="card flex items-center gap-3 cursor-pointer hover:ring-2 ring-primary-200 transition-all" @click="scope = 'all'">
        <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-xl">📚</div>
        <div><p class="text-xl font-bold">{{ stats.published }}</p><p class="text-xs text-surface-500">已发布课程</p></div>
      </div>
      <div class="card flex items-center gap-3 cursor-pointer hover:ring-2 ring-purple-200 transition-all" @click="scope = 'mine'">
        <div class="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center text-xl">🧑‍🏫</div>
        <div><p class="text-xl font-bold">{{ stats.my_courses }}</p><p class="text-xs text-surface-500">我开设的课</p></div>
      </div>
      <div class="card flex items-center gap-3 cursor-pointer hover:ring-2 ring-green-200 transition-all" @click="scope = 'enrolled'">
        <div class="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center text-xl">🎒</div>
        <div><p class="text-xl font-bold">{{ stats.my_enrollments }}</p><p class="text-xs text-surface-500">我在学的课</p></div>
      </div>
      <div class="card flex items-center gap-3 cursor-pointer hover:ring-2 ring-orange-200 transition-all" @click="filterStale">
        <div class="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center text-xl">⚠️</div>
        <div><p class="text-xl font-bold">{{ stats.need_update_coursewares }}</p><p class="text-xs text-surface-500">待 AI 更新课件</p></div>
      </div>
    </div>

    <!-- 过滤器 -->
    <div class="card p-4 flex flex-wrap items-center gap-3">
      <div class="flex flex-wrap gap-1.5">
        <button v-for="s in scopes" :key="s.key" @click="scope = s.key"
                :class="['text-xs px-3 py-1.5 rounded-full transition-colors',
                         scope === s.key ? 'bg-primary-600 text-white' : 'bg-surface-100 text-surface-600 hover:bg-surface-200']">
          {{ s.label }}
        </button>
      </div>
      <div class="flex items-center gap-2 ml-auto">
        <input v-model.trim="q" @keydown.enter="reload" class="input-field text-sm w-56 py-1.5"
               placeholder="搜索课程名 / 简介 / 领域 / 编号" />
        <button @click="reload" class="text-sm px-3 py-1.5 rounded-lg bg-surface-100 hover:bg-surface-200">搜索</button>
      </div>
    </div>

    <!-- 列表 -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="card p-5 animate-pulse">
        <div class="h-6 w-2/3 bg-surface-100 rounded mb-3"></div>
        <div class="h-4 w-full bg-surface-100 rounded mb-2"></div>
        <div class="h-4 w-1/2 bg-surface-100 rounded"></div>
      </div>
    </div>

    <div v-else-if="!items.length" class="card p-12 text-center">
      <p class="text-4xl mb-3">📭</p>
      <p class="text-surface-500 text-sm mb-4">{{ emptyHint }}</p>
      <button v-if="canTeach" @click="$router.push('/courseware-studio')"
              class="px-4 py-2 rounded-lg bg-gradient-to-r from-primary-600 to-accent-600 text-white text-sm mr-2">📽️ 先让 AI 做一份 PPT</button>
      <button v-if="canTeach && scope === 'mine'" @click="openCreate"
              class="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm">开设第一门课程</button>
      <button v-else-if="scope !== 'all'" @click="scope = 'all'; reload()"
              class="px-4 py-2 rounded-lg bg-surface-100 text-sm hover:bg-surface-200">浏览全部公开课程</button>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="c in items" :key="c.id"
           class="card p-5 hover:ring-2 ring-primary-200 transition-all cursor-pointer group flex flex-col"
           @click="goDetail(c)">
        <div class="flex items-start gap-3">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center text-2xl flex-shrink-0">
            {{ c.cover_emoji || '📖' }}
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="font-semibold truncate group-hover:text-primary-600 transition-colors">{{ c.title }}</h3>
            <p class="text-xs text-surface-400 mt-0.5 truncate">
              {{ c.teacher_name }}{{ c.teacher_institution ? ' · ' + c.teacher_institution : '' }}
            </p>
          </div>
          <span v-if="c.status !== 'published'"
                class="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 flex-shrink-0">草稿</span>
        </div>

        <p class="text-sm text-surface-600 mt-3 line-clamp-2 flex-1">{{ c.description || '暂无课程简介' }}</p>

        <div class="mt-3 pt-3 border-t border-surface-100 flex items-center gap-2 flex-wrap text-[11px] text-surface-500">
          <span v-if="c.code" class="px-1.5 py-0.5 rounded bg-surface-100 font-mono">{{ c.code }}</span>
          <span v-if="c.domain" class="px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">{{ c.domain }}</span>
          <span>📀 {{ c.courseware_count }} 件课件</span>
          <span>🎒 {{ c.enroll_count }} 人</span>
          <span v-if="c.chapters?.length">🗂️ {{ c.chapters.length }} 章</span>
          <span v-if="c.project_id" class="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700" title="已关联研究项目">🔗 项目</span>
        </div>

        <div class="mt-3 flex items-center gap-2">
          <span v-if="c.is_enrolled" class="text-[11px] px-2 py-1 rounded-md bg-green-50 text-green-700 border border-green-200">
            ✅ 已选修{{ c.enrollment ? ' · ' + c.enrollment.progress + '%' : '' }}
          </span>
          <span v-else-if="c.is_teacher" class="text-[11px] px-2 py-1 rounded-md bg-primary-50 text-primary-700 border border-primary-200">
            🧑‍🏫 我的课程
          </span>
          <span v-else class="text-[11px] text-surface-400 group-hover:text-primary-500 transition-colors">点击查看 / 选课 →</span>
          <span v-if="staleOf(c)" class="ml-auto text-[11px] px-2 py-1 rounded-md bg-orange-50 text-orange-700 border border-orange-200">
            ⚠️ {{ staleOf(c) }} 件待更新
          </span>
          <button v-if="canTeach && c.is_teacher" @click.stop="removeCourse(c)"
                  :class="['text-[11px] px-2 py-1 rounded-md text-red-500 hover:bg-red-50', staleOf(c) ? '' : 'ml-auto']"
                  title="删除这门课程及其课件、派生资料">🗑 删除</button>
        </div>
      </div>
    </div>

    <!-- ═══ 新建课程 ═══ -->
    <Teleport to="body">
      <div v-if="showCreate" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-start justify-center p-4 overflow-y-auto"
           @click.self="showCreate = false">
        <div class="bg-white dark:bg-surface-900 rounded-xl shadow-2xl w-full max-w-2xl my-8">
          <div class="px-5 py-4 border-b border-surface-100 flex items-center justify-between sticky top-0 bg-white dark:bg-surface-900 rounded-t-xl">
            <h3 class="font-semibold">🎓 新建课程</h3>
            <button @click="showCreate = false" class="text-surface-400 hover:text-surface-600 text-xl leading-none">×</button>
          </div>

          <div class="p-5 space-y-4">
            <!-- 从模板开课：点一下预填名称/编号/领域/大纲骨架，仍可手改（两种模式都可见） -->
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1.5">从模板开课（可选，套用后仍可手改）</label>
              <div class="flex flex-wrap gap-2">
                <button v-for="t in COURSE_TEMPLATES" :key="t.name" type="button" @click="applyCourseTemplate(t)"
                        class="text-xs px-3 py-1.5 rounded-full bg-surface-100 text-surface-700 hover:bg-primary-50 hover:text-primary-700 border border-surface-200 transition-colors">
                  {{ t.cover_emoji }} {{ t.name }}
                </button>
              </div>
            </div>

            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">课程名称 *</label>
              <input v-model.trim="form.title" class="input-field text-sm" placeholder="例如：大语言模型对齐导论" />
            </div>

            <div v-if="isExpert" class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label class="block text-xs font-medium text-surface-600 mb-1">课程编号</label>
                <input v-model.trim="form.code" class="input-field text-sm" placeholder="CS-401" />
              </div>
              <div>
                <label class="block text-xs font-medium text-surface-600 mb-1">领域</label>
                <input v-model.trim="form.domain" class="input-field text-sm" placeholder="人工智能" />
              </div>
              <div>
                <label class="block text-xs font-medium text-surface-600 mb-1">封面 Emoji</label>
                <input v-model.trim="form.cover_emoji" class="input-field text-sm" placeholder="📖" />
              </div>
            </div>

            <div v-if="isExpert">
              <label class="block text-xs font-medium text-surface-600 mb-1">可见性</label>
              <select v-model="form.visibility" class="input-field text-sm">
                <option value="public">公开（学生可浏览）</option>
                <option value="private">仅自己可见</option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">课程简介</label>
              <textarea v-model.trim="form.description" class="input-field text-sm h-20" placeholder="一句话说明课程目标与受众"></textarea>
            </div>

            <div v-if="isExpert">
              <label class="block text-xs font-medium text-surface-600 mb-1">教学大纲（可粘贴任意文本，AI 可自动拆章）</label>
              <textarea v-model="form.syllabus" class="input-field text-sm h-28 font-mono"
                        placeholder="第1章 绪论&#10;1.1 研究背景&#10;1.2 核心挑战&#10;第2章 ..."></textarea>
              <div class="mt-2"><ModeHint scope="outline" /></div>
              <div class="flex flex-wrap items-center gap-2 mt-2">
                <button type="button" @click="aiOutline" :disabled="aiLoading || form.syllabus.trim().length < 10"
                        class="text-xs px-3 py-1.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 disabled:opacity-50">
                  {{ aiLoading ? '🤖 AI 解析中…' : '🤖 AI 自动拆章节' }}
                </button>
                <button type="button" @click="$router.push('/knowledge')"
                        class="text-xs px-3 py-1.5 rounded-md bg-surface-100 text-surface-600 hover:bg-surface-200">
                  📚 先去资料库上传讲义
                </button>
                <span v-if="outlineChapters.length" class="text-[11px] text-green-600">
                  ✓ 已生成 {{ outlineChapters.length }} 章
                </span>
              </div>
            </div>

            <!-- 快速模式：编号/领域/大纲/素材/项目等高级项已折叠，套模板时后台已填好，切专家可展开编辑 -->
            <p v-if="!isExpert" class="text-[11px] text-surface-500 rounded-lg bg-surface-50 px-3 py-2">
              快速模式只填名称与简介即可开课。套用模板后，编号 / 领域 / 大纲已自动填好；需要逐章编辑或 AI 拆章，请
              <button class="text-primary-600 hover:underline" @click="appStore.setMode('expert')">切到专家模式</button>。
            </p>

            <!-- 联动：开课素材来源（题目/报告/项目/资料/技能） -->
            <MaterialSourcePicker v-if="isExpert" v-model="form.sources" :preselect="preselect" />

            <!-- 联动：关联研究项目 -->
            <div v-if="isExpert">
              <label class="block text-xs font-medium text-surface-600 mb-1">关联研究项目（可选，课程 AI 会继承项目上下文）</label>
              <select v-model="form.project_id" class="input-field text-sm">
                <option :value="null">不关联</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.title }}</option>
              </select>
            </div>

            <div v-if="isExpert && outlineChapters.length" class="rounded-lg border border-surface-200 p-3 max-h-40 overflow-y-auto">
              <p class="text-xs font-medium mb-2">章节结构预览</p>
              <div v-for="(ch, i) in outlineChapters" :key="i" class="text-[11px] mb-1.5">
                <span class="font-medium">第{{ i + 1 }}章 {{ ch.title }}</span>
                <span v-if="ch.points?.length" class="text-surface-500"> — {{ ch.points.join('、') }}</span>
              </div>
            </div>
          </div>

          <div class="px-5 py-4 border-t border-surface-100 flex items-center justify-between">
            <span v-if="createMsg" class="text-xs text-red-500">{{ createMsg }}</span>
            <div class="flex gap-2 ml-auto">
              <button @click="showCreate = false" class="px-4 py-2 rounded-lg text-sm bg-surface-100 hover:bg-surface-200">取消</button>
              <button @click="submitCreate" :disabled="creating || !form.title"
                      class="px-4 py-2 rounded-lg text-sm bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50">
                {{ creating ? '创建中…' : '创建课程' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { courseApi, type Course, type Chapter, type MaterialSelection } from '@/api/modules/courses'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { useProjectStore } from '@/stores/project'
import MaterialSourcePicker from '@/components/course/MaterialSourcePicker.vue'
import ModeHint from '@/components/common/ModeHint.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const appStore = useAppStore()
const projectStore = useProjectStore()
const { projects } = storeToRefs(projectStore)

const TEACHER_ROLES = ['teacher', 'researcher', 'admin']
const canTeach = computed(() => TEACHER_ROLES.includes(auth.user?.role || ''))
const isExpert = computed(() => appStore.mode === 'expert')

/** 开课模板：点一下预填名称/编号/领域/大纲骨架，仍可手改 */
interface CourseTemplate {
  name: string; title: string; code: string; domain: string
  cover_emoji: string; description: string; syllabus: string
}
const COURSE_TEMPLATES: CourseTemplate[] = [
  { name: '人工智能导论', title: '人工智能导论', code: 'AI-101', domain: '人工智能', cover_emoji: '🤖',
    description: '面向本科生的 AI 入门课，建立直觉、破除误传、上手常用工具。',
    syllabus: '第1章 什么是人工智能\n第2章 机器学习基础直觉\n第3章 大模型与提示词\n第4章 AI 的边界与伦理' },
  { name: 'Python 编程基础', title: 'Python 编程基础', code: 'CS-101', domain: '计算机科学', cover_emoji: '🐍',
    description: '从零掌握 Python 语法与基本编程思维，配套练习与项目。',
    syllabus: '第1章 变量与类型\n第2章 分支与循环\n第3章 函数与模块\n第4章 文件与异常\n第5章 综合小项目' },
  { name: '数据思维入门', title: '数据思维入门', code: 'DS-101', domain: '数据科学', cover_emoji: '📊',
    description: '不写代码也能懂：如何看数据、防被图表忽悠、用数据做决策。',
    syllabus: '第1章 数据从哪来\n第2章 平均与分布\n第3章 相关不是因果\n第4章 图表怎么误人' },
]
function applyCourseTemplate(t: CourseTemplate) {
  form.title = t.title
  form.code = t.code
  form.domain = t.domain
  form.cover_emoji = t.cover_emoji
  form.description = t.description
  form.syllabus = t.syllabus
  appStore.showToast(`已套用开课模板「${t.name}」`, 'success')
}

const loading = ref(false)
const items = ref<Course[]>([])
const total = ref(0)
const q = ref((route.query.q as string) || '')
const scope = ref<'all' | 'mine' | 'enrolled'>((route.query.scope as any) || 'all')
const wantStale = ref(false)

const scopes = [
  { key: 'all' as const, label: '🌐 公开课程' },
  { key: 'mine' as const, label: '🧑‍🏫 我教的' },
  { key: 'enrolled' as const, label: '🎒 我学的' },
]

const stats = reactive({ published: 0, my_courses: 0, my_enrollments: 0, total_slides: 0, need_update_coursewares: 0, ai_generated_coursewares: 0 })

const emptyHint = computed(() => {
  if (q.value) return `没有匹配「${q.value}」的课程`
  if (scope.value === 'mine') return canTeach.value ? '还没有开设课程，点击右上角新建' : '当前账号不是教师身份，无法开课'
  if (scope.value === 'enrolled') return '还没有选修课程，去「公开课程」里挑一门吧'
  return '暂时还没有已发布的课程'
})

function staleOf(c: Course) {
  const list = c.coursewares || []
  return list.filter(w => {
    const s = w.staleness?.summary
    return s && (s.stale || s.needs_update || s.risky || s.high_risk)
  }).length
}

function filterStale() {
  if (!canTeach.value) { scope.value = 'all' } else { scope.value = 'mine' }
  wantStale.value = true
  reload()
}

async function reload() {
  loading.value = true
  try {
    const res = await courseApi.list({ q: q.value, scope: scope.value, limit: 60 })
    let list = res.data.items || []
    if (wantStale.value) {
      list = list.filter(c => (c.coursewares || []).some(w => (w.staleness?.summary?.total ?? 0) > 0 || Object.keys(w.staleness || {}).length > 1))
      wantStale.value = false
    }
    items.value = list
    total.value = res.data.total
  } catch (e: any) {
    console.error(e)
  } finally { loading.value = false }
}

async function loadStats() {
  try { Object.assign(stats, (await courseApi.stats()).data) } catch { /* ignore */ }
}

/** 卡片上直接删课：不需再进详情页找删除入口（草稿课往往是 AI 自动建的，更需要快速清理） */
async function removeCourse(c: Course) {
  if (!confirm(`确定删除课程「${c.title}」？\n\n其课件、渲染图与派生到资料库的文档会一并清理，且不可恢复。`)) return
  if (c.status === 'published' && !confirm('这门课已发布，学生可能正在学。再确认一次：真的要删除吗？')) return
  try {
    await courseApi.remove(c.id)
    await Promise.all([reload(), loadStats()])
  } catch (e: any) {
    alert(e?.response?.data?.detail || '删除失败，请稍后重试')
  }
}

function goDetail(c: Course) {
  // 只有 1 件课件时直达阅读器，减少一次点击
  const cws = c.coursewares || []
  if (cws.length === 1 && cws[0].status === 'ready') router.push(`/course/${c.id}/read/${cws[0].id}`)
  else router.push(`/course/${c.id}`)
}

// ═══ 新建课程 ═══
const showCreate = ref(false)
const creating = ref(false)
const aiLoading = ref(false)
const createMsg = ref('')
const outlineChapters = ref<Chapter[]>([])
const preselect = ref<MaterialSelection | null>(null)
const form = reactive<{
  title: string; code: string; description: string; syllabus: string; domain: string
  cover_emoji: string; visibility: string; project_id: number | null; sources: MaterialSelection
}>({
  title: '', code: '', description: '', syllabus: '', domain: '', cover_emoji: '📖',
  visibility: 'public', project_id: null, sources: {},
})

function openCreate() {
  showCreate.value = true
  createMsg.value = ''
  outlineChapters.value = []
  if (!projects.value?.length) projectStore.fetchProjects().catch(() => {})
  // 从其它模块带参进来（资料库/项目详情/题目/技能页「用来开课」）
  const q = route.query
  const src: MaterialSelection = {}
  if (typeof queryStr(q.docIds) === 'string') src.doc_ids = toNums(q.docIds)
  if (typeof queryStr(q.questionIds) === 'string') src.question_ids = toNums(q.questionIds)
  if (typeof queryStr(q.taskIds) === 'string') src.task_ids = toNums(q.taskIds)
  if (typeof queryStr(q.skillIds) === 'string') {
    src.skill_runs = toList(q.skillIds).map(id => ({ skill_id: id }))
  }
  if (typeof queryStr(q.runId) === 'string') src.pipeline_run_id = String(q.runId)
  form.sources = src
  preselect.value = { ...src }
  if (typeof q.title === 'string') form.title = q.title
  if (typeof q.domain === 'string') form.domain = q.domain
  if (typeof q.syllabus === 'string') form.syllabus = q.syllabus
  if (q.projectId) form.project_id = Number(q.projectId) || null
}

function queryStr(v: any) { return typeof v === 'string' && v.trim() ? v.trim() : undefined }
function toList(v: any): string[] { return String(v || '').split(',').map(s => s.trim()).filter(Boolean) }
function toNums(v: any): number[] { return toList(v).map(Number).filter(Boolean) }

async function aiOutline() {
  aiLoading.value = true
  createMsg.value = ''
  try {
    const res = await courseApi.aiOutline({ text: form.syllabus, domain: form.domain, sources: form.sources, mode: appStore.mode })
    const d = res.data
    outlineChapters.value = d.chapters || []
    if (d.title && !form.title) form.title = d.title
    if (d.domain && !form.domain) form.domain = d.domain
    if (!outlineChapters.value.length) createMsg.value = 'AI 未能解析出章节，请检查大纲格式或手动填写'
  } catch (e: any) {
    createMsg.value = e?.response?.data?.detail || 'AI 解析失败'
  } finally { aiLoading.value = false }
}

async function submitCreate() {
  creating.value = true
  createMsg.value = ''
  try {
    const res = await courseApi.create({
      ...form, chapters: outlineChapters.value,
    } as any)
    showCreate.value = false
    router.push(`/course/${res.data.id}?new=1`)
  } catch (e: any) {
    createMsg.value = e?.response?.data?.detail || e?.message || '创建失败'
  } finally { creating.value = false }
}

watch(scope, reload)
watch(() => route.query.scope, (v) => { if (typeof v === 'string' && v !== scope.value) scope.value = v as any })

onMounted(async () => {
  await Promise.all([loadStats(), reload()])
  // 从 CommandPalette / ProjectDetail 跳转直接开新建框
  if (route.query.create === '1') openCreate()
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
