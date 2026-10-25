<template>
  <div class="space-y-5 animate-fade-in">
    <!-- 头部 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold flex items-center gap-2">📽️ 课件工坊</h1>
        <p class="text-sm text-surface-500 mt-1">
          不用先建课程 —— 给一个主题，AI 直接产出整套 PPT 课件，可下载 <span class="font-mono">.pptx</span> 投影，也能当电子书阅读
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
        <p class="text-[11px] text-surface-500 mt-1.5 leading-relaxed">生成后可 ⬇️ 下载 .pptx、📖 电子书阅读、✏️ 逐页微调，并自动归入一门课程（默认仅自己可见）</p>
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
            <label class="block text-xs font-medium text-surface-600 mb-1">
              课程大纲（可选 · 留空则由 AI 自行拟大纲；也可在课程中心用「AI 拟大纲」生成后粘过来）
            </label>
            <textarea v-model="form.syllabus" rows="3" class="input-field resize-none text-xs font-mono"
                      placeholder="1. 注意力机制的直觉&#10;2. QKV 与缩放点积&#10;3. 多头注意力"></textarea>
          </div>

          <MaterialSourcePicker v-model="form.sources" :preselect="preselect" />

          <div class="flex flex-wrap items-center gap-3 pt-1">
            <button @click="generate" :disabled="busy || !form.topic"
                    class="px-5 py-2.5 rounded-lg bg-gradient-to-r from-primary-600 to-accent-600 text-white text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed">
              {{ busy ? '⏳ AI 正在逐章撰写…' : `🚀 生成课件（约 ${totalPages} 页）` }}
            </button>
            <span v-if="busy" class="text-xs text-surface-500">通常需要 30–120 秒，生成完会自动出现在下方</span>
            <span v-else class="text-xs text-surface-400">也可以按 Ctrl+Enter 直接生成</span>
          </div>

          <p v-if="errMsg" class="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{{ errMsg }}</p>
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
              <button v-if="result.courseware_id" @click="goReader"
                      class="text-xs px-3 py-2 rounded-lg bg-white border border-surface-200 hover:bg-surface-50">📖 电子书阅读</button>
              <button v-if="result.courseware_id" @click="$router.push(`/course/${result.course_id}`)"
                      class="text-xs px-3 py-2 rounded-lg bg-white border border-surface-200 hover:bg-surface-50">🎓 发布课程</button>
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
              <a :href="coursewareApi.exportUrl(h.id)" :download="`课件_${h.id}.pptx`"
                 class="text-[10px] px-2 py-1 rounded bg-primary-50 text-primary-700 hover:bg-primary-100 flex-1 text-center">⬇️ pptx</a>
              <button @click="reuse(h)" class="text-[10px] px-2 py-1 rounded bg-purple-50 text-purple-700 hover:bg-purple-100"
                      title="按同样设置再生成一份">↺</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MaterialSourcePicker from '@/components/course/MaterialSourcePicker.vue'
import SlidePage from '@/components/course/SlidePage.vue'
import { useAuthStore } from '@/stores/auth'
import {
  courseApi, coursewareApi,
  type AiCoursewareItem, type Course, type DeckResult, type MaterialSelection, type SlideMeta,
} from '@/api/modules/courses'

const STYLES = ['标准', '精炼讲稿', '详尽讲义', '研究进展', '科普通识']
const AUDIENCES = ['本科生', '研究生', '初学者', '企业内训', '评审专家']
const TEACHER_ROLES = ['teacher', 'researcher', 'admin']

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const canTeach = computed(() => TEACHER_ROLES.includes(authStore.user?.role || ''))

const form = reactive({
  topic: '', title: '', domain: '', syllabus: '',
  chapter_count: 6, slides_per_chapter: 4, style: '标准', audience: '本科生',
  course_id: null as number | null, sources: {} as MaterialSelection,
})

const busy = ref(false)
const errMsg = ref('')
const result = ref<DeckResult | null>(null)
const slides = ref<SlideMeta[]>([])
const previewLoading = ref(false)
const showAll = ref(false)
const myCourses = ref<Course[]>([])
const history = ref<AiCoursewareItem[]>([])
const historyLoading = ref(false)

const totalPages = computed(() => 1 + Math.max(1, form.chapter_count) * Math.max(1, form.slides_per_chapter))
const activeCwId = computed(() => result.value?.courseware_id || 0)
const shownSlides = computed(() => (showAll.value ? slides.value : slides.value.slice(0, 6)))
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

async function generate() {
  errMsg.value = ''
  if (!form.topic) { errMsg.value = '请先填写讲授主题'; return }
  busy.value = true
  try {
    const res = await coursewareApi.quickGenerate({
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
    })
    result.value = res.data
    if (res.data.courseware_id) await loadPreview(res.data.courseware_id)
    await Promise.all([loadHistory(), loadMyCourses()])
  } catch (e: any) {
    errMsg.value = e?.response?.data?.detail || `生成失败：${e?.message || '未知错误'}`
  } finally { busy.value = false }
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
  if (canTeach.value) { loadMyCourses(); loadHistory() }
})
</script>
