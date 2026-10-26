<template>
  <div class="space-y-5 animate-fade-in">
    <!-- 头部 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold flex items-center gap-2">📽️ 课件工坊</h1>
        <p class="text-sm text-surface-500 mt-1">
          不用先建课程 —— 给一个主题，AI 直接产出整套 PPT 课件（全程进度可视），可下载 <span class="font-mono">.pptx</span> 投影，
          也能按封面/目录/分章在线读电子书、导出 PDF/EPUB 送手机，还能生成学生/教师讲义（Word / PDF）直接打印
        </p>
      </div>
      <button @click="$router.push('/courses')"
              class="text-sm px-3 py-1.5 rounded-lg bg-surface-100 hover:bg-surface-200">🎓 课程中心</button>
    </div>

    <!-- 功能提示：三步就能拿到 PPT -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <div class="card p-4">
        <p class="text-xs font-semibold text-primary-600">第 1 步 · 说主题</p>
        <p class="text-[11px] text-surface-500 mt-1.5 leading-relaxed">填一个讲授主题（如「Transformer 注意力机制」），设章节数与每章页数，AI 自动拟大纲</p>
      </div>
      <div class="card p-4">
        <p class="text-xs font-semibold text-primary-600">第 2 步 · 喂素材（可选）</p>
        <p class="text-[11px] text-surface-500 mt-1.5 leading-relaxed">勾选资料库原文件、科学问题、研究报告、项目对话、流水线产出、技能结果，让课件建立在你已有的东西之上</p>
      </div>
      <div class="card p-4">
        <p class="text-xs font-semibold text-primary-600">第 3 步 · 拿课件</p>
        <p class="text-[11px] text-surface-500 mt-1.5 leading-relaxed">生成时实时显示阶段/章节/页数进度；完成后 ⬇️ .pptx、📖 在线电子书（也可导 PDF/EPUB）、📄 学生或教师讲义（Word/PDF）、✏️ 逐页微调，并自动归入一门课程（默认仅自己可见）</p>
      </div>
    </div>

    <div v-if="!canTeach" class="card p-8 text-center">
      <p class="text-3xl mb-3">🔒</p>
      <p class="text-sm text-surface-600">课件工坊面向教师 / 研究员开放，当前账号角色：<span class="font-medium">{{ authStore.user?.role || '未知' }}</span></p>
      <p class="text-xs text-surface-400 mt-2">可以在课程中心浏览、选课与阅读课件</p>
    </div>

    <div v-else class="grid grid-cols-1 xl:grid-cols-3 gap-5">
      <!-- ═══ 生成表单 ═══ -->
      <div class="xl:col-span-2 space-y-4">
        <div class="card p-5 space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1">🎯 讲授主题 <span class="text-red-500">*</span></label>
            <textarea v-model.trim="form.topic" rows="2" class="input-field resize-none"
                      placeholder="例如：大模型推理时的键值缓存优化 / 特征值分解与 PageRank 排序"
                      @keydown.ctrl.enter="generate"></textarea>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">课件标题（留空自动生成）</label>
              <input v-model.trim="form.title" class="input-field text-sm py-1.5" placeholder="第一章 注意力机制" />
            </div>
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">领域</label>
              <input v-model.trim="form.domain" class="input-field text-sm py-1.5" placeholder="计算机科学 / 数学…" />
            </div>
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">挂到我的课程（可选）</label>
              <select v-model="form.course_id" class="input-field text-sm py-1.5">
                <option :value="null">🆕 新建一门私有课程承载</option>
                <option v-for="c in myCourses" :key="c.id" :value="c.id">{{ c.title }}</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">章节数</label>
              <input v-model.number="form.chapter_count" type="number" min="1" max="20" class="input-field text-sm py-1.5" />
            </div>
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">每章页数</label>
              <input v-model.number="form.slides_per_chapter" type="number" min="1" max="12" class="input-field text-sm py-1.5" />
            </div>
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">风格</label>
              <select v-model="form.style" class="input-field text-sm py-1.5">
                <option v-for="s in STYLES" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">受众</label>
              <select v-model="form.audience" class="input-field text-sm py-1.5">
                <option v-for="a in AUDIENCES" :key="a" :value="a">{{ a }}</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-surface-600 mb-1">🧠 生成模型（可选）</label>
            <div class="flex items-center gap-2">
              <select v-model="form.model" class="input-field text-sm py-1.5 max-w-xs">
                <option value="">🤖 默认模型（{{ defaultModel || '后端配置' }}）</option>
                <option v-for="m in models" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
              <span v-if="selectedModelDesc" class="text-[11px] text-surface-400">{{ selectedModelDesc }}</span>
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-surface-600 mb-1">
              课程大纲（可选 · 留空则由 AI 自行拟大纲；也可在课程中心用「AI 拟大纲」生成后粘过来）
            </label>
            <textarea v-model="form.syllabus" rows="3" class="input-field resize-none text-xs font-mono"
                      placeholder="1. 注意力机制的直觉&#10;2. QKV 与缩放点积&#10;3. 多头注意力"></textarea>
          </div>

          <MaterialSourcePicker v-model="form.sources" :preselect="preselect" />

          <div class="flex flex-wrap items-center gap-3 pt-1">
            <button v-if="!busy" @click="generate" :disabled="!form.topic"
                    class="px-5 py-2.5 rounded-lg bg-gradient-to-r from-primary-600 to-accent-600 text-white text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed">
              🚀 生成课件（约 {{ totalPages }} 页）
            </button>
            <button v-else @click="stop" :disabled="!job?.job_id || cancelling"
                    class="px-5 py-2.5 rounded-lg bg-red-50 text-red-600 border border-red-200 text-sm font-medium hover:bg-red-100 transition-colors disabled:opacity-40">
              {{ cancelling ? '⏹ 正在停止…' : '⏹ 停止生成' }}
            </button>
            <span v-if="busy" class="text-xs text-surface-500">实时显示进度，可随时停止；停止后调参再重新发起</span>
            <span v-else class="text-xs text-surface-400">也可以按 Ctrl+Enter 直接生成</span>
          </div>

          <!-- ═══ 生成进度：阶段 / 章节 / 页数 全部来自后端真实上报 ═══ -->
          <div v-if="busy && job" class="rounded-xl border border-primary-100 bg-gradient-to-b from-primary-50/70 to-white p-4 space-y-3">
            <div class="flex items-center justify-between gap-2">
              <p class="text-sm font-medium text-primary-700 truncate">{{ job.message || '生成中…' }}</p>
              <p class="text-xs font-mono text-surface-500 shrink-0">{{ job.percent }}% · {{ elapsed }}s</p>
            </div>
            <div class="h-2.5 rounded-full bg-surface-100 overflow-hidden">
              <div class="h-full rounded-full bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-700"
                   :style="{ width: `${job.percent}%` }"></div>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="(s, i) in STAGE_STEPS" :key="s.key"
                    class="text-[10px] px-2 py-1 rounded-full border transition-colors"
                    :class="i < stageIndex ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                            : i === stageIndex ? 'bg-primary-600 border-primary-600 text-white'
                            : 'bg-white border-surface-200 text-surface-400'">
                {{ i < stageIndex ? '✓' : i + 1 }} {{ s.label }}
              </span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-[11px]">
              <div class="rounded-lg bg-white border border-surface-100 px-3 py-2">
                章节 <b class="font-mono text-primary-700">{{ job.chapters_done }}/{{ job.chapters_total || form.chapter_count }}</b>
              </div>
              <div class="rounded-lg bg-white border border-surface-100 px-3 py-2">
                已产出页 <b class="font-mono text-primary-700">{{ job.slides_done }}</b>/<span class="font-mono">{{ job.slides_total || totalPages }}</span>
              </div>
            </div>
            <ul v-if="stageLog.length" class="text-[10px] text-surface-500 space-y-0.5 max-h-28 overflow-y-auto pr-1">
              <li v-for="(l, i) in stageLog" :key="i">{{ l }}</li>
            </ul>
          </div>

          <p v-if="errMsg" class="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{{ errMsg }}</p>
          <p v-if="noticeMsg" class="text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">{{ noticeMsg }}</p>
        </div>

        <!-- ═══ 生成结果 ═══ -->
        <div v-if="result" class="card overflow-hidden">
          <div class="px-5 py-4 bg-gradient-to-r from-primary-50 to-accent-50 border-b border-surface-100 flex flex-wrap items-center gap-3">
            <div class="min-w-0 flex-1">
              <p class="font-semibold truncate">✅ {{ result.title }}</p>
              <p class="text-[11px] text-surface-500 mt-0.5">
                {{ result.slide_count }} 页 · {{ result.chapters?.length || 0 }} 章 · 成本 ¥{{ (result.cost || 0).toFixed(4) }}
                <span v-if="result.sources_used?.length" class="ml-1 text-purple-600">· 🧩 引用 {{ result.sources_used.length }} 个素材源</span>
                · 已归入 <button class="text-primary-600 hover:underline" @click="$router.push(`/course/${result.course_id}`)">{{ result.course_title }}</button>
              </p>
            </div>
            <div class="flex flex-wrap gap-2">
              <a v-if="result.courseware_id" :href="coursewareApi.exportUrl(result.courseware_id)"
                 :download="`${result.title || '课件'}.pptx`"
                 class="text-xs px-3 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 font-medium">
                ⬇️ 下载 .pptx
              </a>
              <button v-if="result.courseware_id"
                      @click="$router.push({ name: 'CoursewareEbook', params: { courseId: result.course_id || 0, cwId: result.courseware_id } })"
                      class="text-xs px-3 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
                      title="在线电子书：封面 + 目录 + 分章阅读，可调字号/夜间模式">📖 在线电子书</button>
              <a v-if="result.courseware_id" :href="coursewareApi.ebookUrl(result.courseware_id, 'pdf')" target="_blank" rel="noopener"
                 class="text-xs px-2.5 py-2 rounded-lg bg-white border border-surface-200 hover:bg-surface-50 text-surface-500"
                 title="电子书 PDF：封面 + 目录 + 页码，可打印、手机可读">PDF</a>
              <a v-if="result.courseware_id" :href="coursewareApi.ebookUrl(result.courseware_id, 'epub')" target="_blank" rel="noopener"
                 class="text-xs px-2.5 py-2 rounded-lg bg-white border border-surface-200 hover:bg-surface-50 text-surface-500"
                 title="EPUB：导入手机/阅读器">EPUB</a>
              <a v-if="result.courseware_id" :href="coursewareApi.handoutUrl(result.courseware_id, 'student', 'docx')" target="_blank" rel="noopener"
                 class="text-xs px-3 py-2 rounded-lg bg-white border border-surface-200 hover:bg-surface-50"
                 title="学生讲义 Word：要点 + 讲透 + 案例 + 笔记留白 + 思考题">📄 学生讲义</a>
              <a v-if="result.courseware_id" :href="coursewareApi.handoutUrl(result.courseware_id, 'student', 'pdf')" target="_blank" rel="noopener"
                 class="text-xs px-2.5 py-2 rounded-lg bg-white border border-surface-200 hover:bg-surface-50 text-surface-500"
                 title="学生讲义 PDF：直接打印">PDF</a>
              <a v-if="result.courseware_id" :href="coursewareApi.handoutUrl(result.courseware_id, 'teacher', 'docx')" target="_blank" rel="noopener"
                 class="text-xs px-3 py-2 rounded-lg bg-white border border-surface-200 hover:bg-surface-50"
                 title="教师讲义 Word：含讲透、讲师速记、时长建议与陈旧警示">🗒 教师讲义</a>
              <button v-if="result.courseware_id" @click="goReader"
                      class="text-xs px-3 py-2 rounded-lg bg-white border border-surface-200 hover:bg-surface-50">📖 逐页阅读</button>
              <button v-if="result.courseware_id" @click="$router.push(`/course/${result.course_id}`)"
                      class="text-xs px-3 py-2 rounded-lg bg-white border border-surface-200 hover:bg-surface-50">🎓 发布课程</button>
              <button v-if="result.courseware_id" @click="removeResult" :disabled="deleting"
                      class="text-xs px-2.5 py-2 rounded-lg text-red-500 hover:bg-red-50 disabled:opacity-40">🗑 删除这份</button>
            </div>
          </div>

          <div v-if="result.sources_used?.length" class="px-5 py-2.5 border-b border-surface-100 flex flex-wrap gap-1.5">
            <span v-for="(s, i) in result.sources_used" :key="i"
                  class="text-[10px] px-2 py-0.5 rounded-full bg-surface-100 text-surface-600" :title="`注入 ${s.chars} 字符`">
              {{ kindIcon(s.kind) }} {{ s.label }}
            </span>
          </div>

          <div class="p-5 space-y-4">
            <div v-if="previewLoading" class="text-xs text-surface-400 py-6 text-center">⏳ 加载预览…</div>
            <template v-else>
              <SlidePage v-for="s in shownSlides" :key="s.slide_index" :slide="s" :cw-id="activeCwId" />
              <button v-if="!showAll && slides.length > shownSlides.length" @click="showAll = true"
                      class="w-full text-xs py-2.5 rounded-lg bg-surface-50 hover:bg-surface-100 text-surface-600">
                展开全部 {{ slides.length }} 页（当前显示 {{ shownSlides.length }} 页）
              </button>
            </template>
          </div>
        </div>

        <div v-else-if="!busy" class="card p-10 text-center">
          <p class="text-4xl mb-3">🎬</p>
          <p class="text-sm text-surface-500">生成的课件会出现在这里，左边填主题 → 点「🚀 生成课件」就行</p>
          <p class="text-[11px] text-surface-400 mt-2">想改已有课件？去 <button class="text-primary-600 hover:underline" @click="$router.push('/courses')">课程中心</button> 的「AI 体检 / AI 更新」</p>
        </div>
      </div>

      <!-- ═══ 历史 ═══ -->
      <div class="card p-4 h-fit xl:sticky xl:top-4">
        <div class="flex items-center justify-between mb-3">
          <p class="text-sm font-semibold">🗂️ 我生成过的课件</p>
          <button @click="loadHistory" class="text-[11px] text-surface-400 hover:text-primary-600">↻ 刷新</button>
        </div>
        <div v-if="historyLoading" class="text-xs text-surface-400 py-6 text-center">⏳ 加载中…</div>
        <div v-else-if="!history.length" class="text-xs text-surface-400 py-6 text-center">还没有记录，先生成一份吧</div>
        <div v-else class="space-y-2 max-h-[560px] overflow-y-auto pr-1">
          <div v-for="h in history" :key="h.id" class="rounded-lg border border-surface-100 p-3 hover:border-primary-200 transition-colors">
            <p class="text-xs font-medium truncate" :title="h.title">{{ h.title }}</p>
            <p class="text-[10px] text-surface-400 mt-1 truncate">{{ h.course_title }} · {{ h.slide_count }} 页 · v{{ h.version }} · {{ fmtTime(h.created_at) }}</p>
            <div class="flex gap-1.5 mt-2">
              <button @click="$router.push(h.reader_url)"
                      class="text-[10px] px-2 py-1 rounded bg-surface-100 hover:bg-surface-200 flex-1">📖 阅读</button>
              <button @click="$router.push({ name: 'CoursewareEbook', params: { courseId: h.course_id, cwId: h.id } })"
                      class="text-[10px] px-2 py-1 rounded bg-indigo-50 text-indigo-700 hover:bg-indigo-100 flex-1" title="在线电子书">📕</button>
              <a :href="coursewareApi.handoutUrl(h.id, 'student', 'docx')" target="_blank" rel="noopener"
                 class="text-[10px] px-2 py-1 rounded bg-surface-100 hover:bg-surface-200 flex-1 text-center" title="学生讲义 Word">📄</a>
              <a :href="coursewareApi.exportUrl(h.id)" :download="`课件_${h.id}.pptx`"
                 class="text-[10px] px-2 py-1 rounded bg-primary-50 text-primary-700 hover:bg-primary-100 flex-1 text-center">⬇️ pptx</a>
              <button @click="reuse(h)" class="text-[10px] px-2 py-1 rounded bg-purple-50 text-purple-700 hover:bg-purple-100"
                      title="按同样设置再生成一份">↺</button>
              <button @click="removeHistory(h)" :disabled="deleting"
                      class="text-[10px] px-2 py-1 rounded text-red-500 hover:bg-red-50 disabled:opacity-40"
                      title="删除这份课件">🗑</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MaterialSourcePicker from '@/components/course/MaterialSourcePicker.vue'
import SlidePage from '@/components/course/SlidePage.vue'
import { useAuthStore } from '@/stores/auth'
import {
  courseApi, coursewareApi,
  type AiCoursewareItem, type Course, type DeckResult, type GenerateJobStatus,
  type GenerateModelItem, type MaterialSelection, type SlideMeta,
} from '@/api/modules/courses'

const STYLES = ['标准', '精炼讲稿', '详尽讲义', '研究进展', '科普通识']
const AUDIENCES = ['本科生', '研究生', '初学者', '企业内训', '评审专家']
const TEACHER_ROLES = ['teacher', 'researcher', 'admin']
/** 与后端 _build_deck / generate_deck 的 stage 上报一一对应，用来画步骤条 */
const STAGE_STEPS = [
  { key: 'material', label: '聚合素材' },
  { key: 'outline', label: '拟大纲' },
  { key: 'chapter', label: '逐章撰写' },
  { key: 'summary', label: '小结与思考题' },
  { key: 'render', label: '逐页配图' },
  { key: 'persist', label: '落库归档' },
]

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const canTeach = computed(() => TEACHER_ROLES.includes(authStore.user?.role || ''))

const form = reactive({
  topic: '', title: '', domain: '', syllabus: '',
  chapter_count: 6, slides_per_chapter: 5, style: '标准', audience: '本科生',
  course_id: null as number | null, sources: {} as MaterialSelection,
  model: '',
})
const models = ref<GenerateModelItem[]>([])
const defaultModel = ref('')
const selectedModelDesc = computed(() => models.value.find(m => m.value === form.model)?.desc || '')

const busy = ref(false)
const errMsg = ref('')
const noticeMsg = ref('')
const cancelling = ref(false)
const result = ref<DeckResult | null>(null)
const slides = ref<SlideMeta[]>([])
const previewLoading = ref(false)
const showAll = ref(false)
const myCourses = ref<Course[]>([])
const history = ref<AiCoursewareItem[]>([])
const historyLoading = ref(false)

// 生成作业的真实进度（后端按阶段/章节/页上报，前端轮询驱动进度条）
const job = ref<GenerateJobStatus | null>(null)
const stageLog = ref<string[]>([])
const elapsed = ref(0)
let pollTimer: number | null = null
let tickTimer: number | null = null

const totalPages = computed(() =>
  1 + Math.max(1, form.chapter_count) * (Math.max(1, form.slides_per_chapter) + 1) + 1)
const activeCwId = computed(() => result.value?.courseware_id || 0)
const shownSlides = computed(() => (showAll.value ? slides.value : slides.value.slice(0, 6)))
const stageIndex = computed(() => {
  const s = job.value?.stage || 'queued'
  const i = STAGE_STEPS.findIndex(x => x.key === s)
  if (i >= 0) return i
  if (s === 'assemble') return 3
  if (s === 'persist' || s === 'done') return STAGE_STEPS.length - 1
  return 0
})
const preselect = computed<MaterialSelection | null>(() => {
  const q = route.query
  const out: MaterialSelection = {}
  if (q.doc_ids) out.doc_ids = String(q.doc_ids).split(',').map(Number).filter(n => !Number.isNaN(n))
  if (q.question_ids) out.question_ids = String(q.question_ids).split(',').map(Number).filter(n => !Number.isNaN(n))
  if (q.task_ids) out.task_ids = String(q.task_ids).split(',').map(Number).filter(n => !Number.isNaN(n))
  if (q.pipeline_run_id) out.pipeline_run_id = String(q.pipeline_run_id)
  if (q.project_id) {
    out.project_id = Number(q.project_id)
    if (q.chat === '1') out.chat_project_id = Number(q.project_id)
  }
  return Object.keys(out).length ? out : null
})

function kindIcon(kind: string) {
  return ({ document: '📄', question: '❓', report: '📑', project: '📁', chat: '💬', pipeline: '⚡', skill: '🛠️' } as Record<string, string>)[kind] || '🧩'
}
function fmtTime(iso: string) {
  if (!iso) return ''
  return iso.slice(0, 16).replace('T', ' ')
}

async function loadPreview(cwId: number) {
  previewLoading.value = true
  showAll.value = false
  try {
    const r = await coursewareApi.detail(cwId)
    slides.value = r.data.slides || []
  } catch (e) {
    console.warn('preview load failed', e)
    slides.value = []
  } finally { previewLoading.value = false }
}

function goReader() {
  if (result.value?.reader_url) router.push(result.value.reader_url)
}

// ═══ 删除（结果区 / 历史列表） ═══
const deleting = ref(false)
async function removeResult() {
  const cwId = result.value?.courseware_id
  if (!cwId) return
  await removeCw(cwId, result.value?.title || '')
  result.value = null
  slides.value = []
}
async function removeHistory(h: AiCoursewareItem) {
  await removeCw(h.id, h.title)
  if (result.value?.courseware_id === h.id) {
    result.value = null
    slides.value = []
  }
  await loadHistory()
}
async function removeCw(id: number, title: string) {
  if (!confirm(`确定删除《${title || '这份课件'}》？\n\n渲染图、导出缓存与派生文档会一并清理，且不可恢复。`)) return
  deleting.value = true
  try {
    await coursewareApi.remove(id)
    await loadMyCourses()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '删除失败，请稍后重试')
  } finally {
    deleting.value = false
  }
}

function stopTimers() {
  if (pollTimer) { window.clearInterval(pollTimer); pollTimer = null }
  if (tickTimer) { window.clearInterval(tickTimer); tickTimer = null }
}

/** 拉一次作业状态：进度只增不减，完成后停下轮询并接结果 */
async function pollJob(jobId: string) {
  try {
    const r = await coursewareApi.generateStatus(jobId)
    const s = r.data
    job.value = { ...s, percent: Math.max(s.percent || 0, job.value?.percent || 0) }
    if (s.message && !stageLog.value.some(l => l.endsWith(s.message))) {
      stageLog.value.push(`+${elapsed.value}s ${s.message}`)
      if (stageLog.value.length > 40) stageLog.value.shift()
    }
    if (s.status === 'done' && s.result) {
      stopTimers()
      busy.value = false
      cancelling.value = false
      result.value = s.result
      job.value = { ...s, percent: 100 }
      if (s.result.courseware_id) await loadPreview(s.result.courseware_id)
      await Promise.all([loadHistory(), loadMyCourses()])
    } else if (s.status === 'failed') {
      stopTimers()
      busy.value = false
      cancelling.value = false
      errMsg.value = s.error ? `生成失败：${s.error}` : '生成失败，请重试或换个主题'
    } else if (s.status === 'cancelled') {
      stopTimers()
      busy.value = false
      cancelling.value = false
      noticeMsg.value = '已停止生成。已落库的部分不会计入「我生成过的课件」，调好参数后可直接重新发起。'
    }
  } catch (e: any) {
    if (e?.response?.status === 404) {
      stopTimers()
      busy.value = false
      errMsg.value = '作业记录已过期（服务重启或超过 30 分钟），请查看右侧「我生成过的课件」'
    }
    // 其他异常（网络抖动）保持轮询，不中断生成
  }
}

async function generate() {
  errMsg.value = ''
  noticeMsg.value = ''
  cancelling.value = false
  if (!form.topic) { errMsg.value = '请先填写讲授主题'; return }
  busy.value = true
  result.value = null
  slides.value = []
  stageLog.value = []
  elapsed.value = 0
  job.value = {
    ok: true, job_id: '', status: 'running', stage: 'queued', percent: 1,
    message: '正在提交生成作业…', chapters_done: 0, chapters_total: form.chapter_count,
    slides_done: 0, slides_total: totalPages.value,
  }
  tickTimer = window.setInterval(() => { elapsed.value += 1 }, 1000)
  try {
    const res = await coursewareApi.startGenerate({
      topic: form.topic,
      title: form.title || undefined,
      domain: form.domain || undefined,
      syllabus: form.syllabus || undefined,
      chapter_count: form.chapter_count,
      slides_per_chapter: form.slides_per_chapter,
      style: form.style,
      audience: form.audience,
      course_id: form.course_id,
      sources: form.sources,
      auto_save: true,
      model: form.model || undefined,
    })
    const jobId = res.data.job_id
    if (!jobId) throw new Error('服务端未返回 job_id')
    job.value = { ...job.value, job_id: jobId }
    void pollJob(jobId)
    pollTimer = window.setInterval(() => void pollJob(jobId), 1200)
  } catch (e: any) {
    stopTimers()
    busy.value = false
    job.value = null
    errMsg.value = e?.response?.data?.detail || `提交失败：${e?.message || '未知错误'}`
  }
}

onUnmounted(stopTimers)

/** 停止当前生成作业（服务端会等当前步骤结束后停下）*/
async function stop() {
  const jobId = job.value?.job_id
  if (!jobId || cancelling.value) return
  cancelling.value = true
  try {
    await coursewareApi.cancelGenerate(jobId)
  } catch (e: any) {
    if (e?.response?.status === 409) {
      // 已结束：下一轮轮询会拉到终态，这里不报错
      cancelling.value = false
    } else {
      cancelling.value = false
      errMsg.value = e?.response?.data?.detail || '停止失败，请重试'
    }
  }
}

async function loadModels() {
  try {
    const r = await coursewareApi.generateModels()
    models.value = r.data?.items || []
    defaultModel.value = r.data?.default || ''
  } catch { /* ignore：下拉会退化为“默认模型” */ }
}

/** 用历史课件的同样参数再跑一次（换主题即可批量出不同章节） */
function reuse(h: AiCoursewareItem) {
  form.title = ''
  form.course_id = h.course_id
  result.value = null
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function loadMyCourses() {
  try {
    const r = await courseApi.list({ scope: 'mine', limit: 50 })
    myCourses.value = r.data?.items || []
  } catch { /* ignore */ }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const r = await coursewareApi.aiMine(30)
    history.value = r.data?.items || []
  } catch { /* ignore */ } finally { historyLoading.value = false }
}

onMounted(() => {
  if (route.query.topic) form.topic = String(route.query.topic)
  if (route.query.course_id) form.course_id = Number(route.query.course_id) || null
  if (canTeach.value) { loadMyCourses(); loadHistory(); loadModels() }
})
</script>
