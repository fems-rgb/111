<template>
  <div class="animate-fade-in space-y-4">
    <!-- ═══ 顶栏 ═══ -->
    <div class="card p-4 sticky top-0 z-20">
      <div class="flex flex-wrap items-center gap-3">
        <button @click="goBack" class="text-sm text-surface-500 hover:text-primary-600 flex items-center gap-1">
          ← {{ meta.course_title || '课程' }}
        </button>
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-lg">{{ meta.cover_emoji || '📖' }}</span>
            <h1 class="font-semibold truncate">{{ meta.title }}</h1>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-surface-100 text-surface-500 font-mono">v{{ meta.version }}</span>
            <span :class="['text-[10px] px-1.5 py-0.5 rounded-full',
                           meta.source_type === 'ai_generated' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700']">
              {{ meta.source_type === 'ai_generated' ? '🤖 AI 生成' : '📊 教师上传' }}
            </span>
          </div>
          <p class="text-[11px] text-surface-500 mt-0.5">
            共 {{ meta.slide_count }} 页 · 文本层 {{ meta.read_size_kb }} KB
            <template v-if="opt.original_kb"> · 原 PPT {{ fmtKB(opt.original_kb * 1024) }} → 首屏仅 {{ opt.first_paint_kb }}KB（↓{{ opt.saved_percent }}%）</template>
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <div class="flex rounded-lg border border-surface-200 overflow-hidden text-xs">
            <button @click="viewMode = 'slide'"
                    :class="['px-2.5 py-1.5', viewMode === 'slide' ? 'bg-primary-600 text-white' : 'bg-white text-surface-600 hover:bg-surface-50']">
              🖥️ 幻灯片
            </button>
            <button @click="viewMode = 'book'"
                    :class="['px-2.5 py-1.5', viewMode === 'book' ? 'bg-primary-600 text-white' : 'bg-white text-surface-600 hover:bg-surface-50']">
              📖 读物
            </button>
          </div>
          <button @click="showVersions = true" class="text-xs px-2.5 py-1.5 rounded-lg bg-surface-100 hover:bg-surface-200">🕘 版本</button>
          <a :href="coursewareApi.ebookUrl(cwId, 'pdf')" target="_blank" rel="noopener"
             class="text-xs px-2.5 py-1.5 rounded-lg bg-surface-100 hover:bg-surface-200"
             title="电子书 PDF：封面 + 目录 + 页码，可打印、手机可读">📕 电子书</a>
          <a :href="coursewareApi.ebookUrl(cwId, 'epub')" target="_blank" rel="noopener"
             class="text-xs px-2 py-1.5 rounded-lg bg-surface-100 hover:bg-surface-200 text-surface-500"
             title="EPUB：导入手机/阅读器，带可跳转目录">EPUB</a>
          <a :href="coursewareApi.handoutUrl(cwId, meta.is_teacher ? 'teacher' : 'student', 'docx')" target="_blank" rel="noopener"
             class="text-xs px-2.5 py-1.5 rounded-lg bg-surface-100 hover:bg-surface-200"
             title="课堂讲义 Word：要点 + 讲透 + 案例，学生版留笔记横线，教师版附速记">📄 讲义</a>
          <a :href="coursewareApi.handoutUrl(cwId, meta.is_teacher ? 'teacher' : 'student', 'pdf')" target="_blank" rel="noopener"
             class="text-xs px-2 py-1.5 rounded-lg bg-surface-100 hover:bg-surface-200 text-surface-500"
             title="讲义 PDF：直接打印">PDF</a>
          <a :href="coursewareApi.exportUrl(cwId)"
             class="text-xs px-2.5 py-1.5 rounded-lg bg-surface-100 hover:bg-surface-200">⬇️ PPTX</a>
          <button v-if="meta.is_teacher" @click="openRefresh"
                  class="text-xs px-3 py-1.5 rounded-lg bg-orange-500 text-white hover:bg-orange-600">
            ✨ AI 更新陈旧内容
          </button>
          <button v-if="meta.is_teacher" @click="removeThis" :disabled="deleting"
                  class="text-xs px-2.5 py-1.5 rounded-lg text-red-500 hover:bg-red-50 disabled:opacity-40"
                  title="删除这份课件及其渲染图、导出缓存">
            🗑 删除
          </button>
        </div>
      </div>

      <!-- 进度 -->
      <div v-if="meta.enrolled" class="mt-3 flex items-center gap-3">
        <div class="flex-1 h-1.5 rounded-full bg-surface-100 overflow-hidden">
          <div class="h-full bg-green-500 transition-all" :style="{ width: progressPct + '%' }"></div>
        </div>
        <span class="text-[11px] text-surface-500 w-24 text-right">已读 {{ readSet.size }}/{{ meta.slide_count }} 页</span>
      </div>
      <div v-else-if="!meta.is_teacher" class="mt-2 text-[11px] text-amber-600">
        💡 选修这门课后即可自动记录学习进度 ·
        <button class="underline" @click="goBack">回到课程页选课</button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-4 items-start">
      <!-- ═══ 目录侧栏 ═══ -->
      <aside class="card p-3 lg:sticky lg:top-32 lg:max-h-[calc(100vh-9rem)] flex flex-col">
        <input v-model.trim="kw" class="input-field text-xs mb-2 py-1.5" placeholder="🔍 搜索课件内容…" />
        <div class="flex-1 overflow-y-auto space-y-0.5 pr-1 -mr-1">
          <button v-for="s in tocList" :key="s.slide_index"
                  @click="jumpTo(s.slide_index)"
                  :class="['w-full text-left px-2 py-1.5 rounded-md text-xs transition-colors flex items-start gap-1.5',
                           s.slide_index === current ? 'bg-primary-50 text-primary-700 font-medium' : 'hover:bg-surface-50 text-surface-600']">
            <span class="text-[10px] text-surface-400 w-5 flex-shrink-0 mt-0.5">{{ s.slide_index + 1 }}</span>
            <span class="flex-1 min-w-0">
              <span class="block truncate">{{ s.title || '(无标题页)' }}</span>
              <span v-if="s.risk_score >= 0.4" class="text-[10px] text-orange-600">⚠️ 疑似过时</span>
              <span v-else-if="s.updated_by_ai" class="text-[10px] text-purple-600">✨ AI 已更新</span>
            </span>
          </button>
          <p v-if="kw && !tocList.length" class="text-xs text-surface-400 py-3 text-center">无匹配页面</p>
        </div>
      </aside>

      <!-- ═══ 主体 ═══ -->
      <main class="space-y-4">
        <div v-if="loading" class="card p-16 text-center text-surface-400 text-sm">⏳ 加载文本层（图片按需加载，所以很快）…</div>

        <!-- 幻灯片模式 -->
        <div v-else-if="viewMode === 'slide' && slides.length" class="space-y-4">
          <SlidePage :slide="slides[current]" :cw-id="cwId" :eager="true" :show-notes="showNotes" />
          <div class="card p-3 flex flex-wrap items-center gap-2 justify-between">
            <div class="flex items-center gap-2">
              <button @click="prev" :disabled="current === 0"
                      class="px-3 py-1.5 rounded-lg text-sm bg-surface-100 hover:bg-surface-200 disabled:opacity-40">← 上一页</button>
              <button @click="next" :disabled="current >= slides.length - 1"
                      class="px-3 py-1.5 rounded-lg text-sm bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40">下一页 →</button>
              <span class="text-xs text-surface-500 ml-1">{{ current + 1 }} / {{ slides.length }} · 方向键 ←/→</span>
              <label class="flex items-center gap-1.5 text-xs text-surface-500 ml-2 cursor-pointer">
                <input type="checkbox" v-model="showNotes" class="accent-primary-600" /> 显示讲者备注
              </label>
            </div>
            <div class="flex items-center gap-2">
              <button @click="askThisSlide" class="text-xs px-2.5 py-1.5 rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200">
                💬 就本页提问
              </button>
              <button v-if="meta.is_teacher && slides[current]?.risk_score >= 0.4" @click="refreshOne(slides[current])"
                      class="text-xs px-2.5 py-1.5 rounded-md bg-orange-50 text-orange-700 hover:bg-orange-100 border border-orange-200">
                ✨ 只更新本页
              </button>
            </div>
          </div>
        </div>

        <!-- 读物模式：连贯电子书 -->
        <div v-else-if="viewMode === 'book'" class="card p-6 md:p-10">
          <div class="max-w-2xl mx-auto space-y-8">
            <div class="pb-4 border-b border-surface-100">
              <p class="text-xs text-surface-400">{{ meta.course_title }}</p>
              <h2 class="text-2xl font-bold mt-1">{{ meta.title }}</h2>
              <p class="text-sm text-surface-500 mt-2">共 {{ meta.slide_count }} 页 · 已转为连贯读物，可搜索、可选中复制</p>
            </div>
            <article v-for="s in slides" :key="s.slide_index" :id="`pg-${s.slide_index}`" class="scroll-mt-36">
              <h3 class="text-lg font-semibold flex items-start gap-2">
                <span class="text-xs text-surface-300 font-mono mt-1.5">{{ String(s.slide_index + 1).padStart(2, '0') }}</span>
                <span>{{ s.title || '（续）' }}</span>
                <span v-if="s.risk_score >= 0.4" class="ml-auto text-[10px] px-1.5 py-0.5 rounded-full bg-orange-50 text-orange-600 flex-shrink-0">⚠️</span>
              </h3>
              <ul class="mt-2 space-y-1.5">
                <li v-for="(b, bi) in s.bullets" :key="bi"
                    :class="[b.level >= 1 ? 'ml-5 text-sm text-surface-600 list-disc' : 'text-[15px] text-surface-800 list-disc marker:text-primary-400']">
                  {{ b.text }}
                </li>
              </ul>
              <table v-if="s.tables?.length" class="mt-3 w-full text-xs border-collapse">
                <tbody>
                  <tr v-for="(row, ri) in s.tables[0]" :key="ri">
                    <td v-for="(cell, ci) in row" :key="ci" class="border border-surface-200 px-2 py-1">{{ cell }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-if="s.has_image" class="mt-3">
                <img :src="coursewareApi.imageUrl(cwId, s.slide_index)" loading="lazy" alt=""
                     class="w-full rounded-lg border border-surface-100 bg-surface-50"
                     @error="onImgError" />
                <p class="text-[10px] text-surface-400 mt-1">🖼️ 本页配图按需加载 · {{ s.image_kb }}KB</p>
              </div>
              <p v-if="s.ai_suggestion" class="mt-2 text-[11px] text-orange-600 bg-orange-50 rounded-md p-2">🤖 {{ s.ai_suggestion }}</p>
            </article>
          </div>
        </div>

        <div v-else class="card p-16 text-center">
          <p class="text-3xl mb-2">📄</p>
          <p class="text-sm text-surface-500">课件暂无可读内容</p>
        </div>
      </main>
    </div>

    <!-- ═══ AI 更新面板（需求 3 + 联动素材） ═══ -->
    <Teleport to="body">
      <div v-if="showRefresh" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-start justify-center p-4 overflow-y-auto"
           @click.self="showRefresh = false">
        <div class="bg-white dark:bg-surface-900 rounded-xl shadow-2xl w-full max-w-2xl my-8">
          <div class="px-5 py-4 border-b border-surface-100 flex items-center justify-between">
            <h3 class="font-semibold">✨ AI 自动更新课件</h3>
            <button @click="showRefresh = false" class="text-surface-400 hover:text-surface-600 text-xl leading-none">×</button>
          </div>
          <div class="p-5 space-y-4">
            <div class="p-3 rounded-lg bg-orange-50 border border-orange-100 text-xs text-orange-800 leading-relaxed">
              大学老师一份课件用很多年 —— AI 会逐页判断数据、文献、案例是否过时，
              只重写有问题的页面，并<span class="font-medium">保留原版本</span>形成版本链，你可以随时对比回退。
            </div>

            <div v-if="riskItems.length" class="rounded-lg border border-surface-200 overflow-hidden">
              <div class="px-3 py-2 bg-surface-50 flex items-center justify-between">
                <span class="text-xs font-medium">体检结果（{{ riskItems.length }} 页疑似过时）</span>
                <label class="flex items-center gap-1.5 text-[11px] cursor-pointer">
                  <input type="checkbox" v-model="onlyRisky" class="accent-primary-600" /> 仅更新疑似过时页
                </label>
              </div>
              <div class="max-h-40 overflow-y-auto">
                <label v-for="s in riskItems" :key="s.slide_index"
                       class="flex items-start gap-2 px-3 py-1.5 hover:bg-surface-50 cursor-pointer text-xs">
                  <input type="checkbox" class="mt-0.5 accent-primary-600"
                         :checked="onlyRisky || picked.includes(s.slide_index)"
                         :disabled="onlyRisky"
                         @change="togglePick(s.slide_index)" />
                  <span class="text-surface-400 w-6">{{ s.slide_index + 1 }}</span>
                  <span class="flex-1 min-w-0">
                    <span class="block truncate">{{ s.title }}</span>
                    <span class="text-[10px] text-orange-600">{{ s.risk_category || '内容陈旧' }} · {{ (s.ai_reason || '').slice(0, 60) }}</span>
                  </span>
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-orange-100 text-orange-700">{{ (s.risk_score * 100).toFixed(0) }}%</span>
                </label>
              </div>
            </div>
            <button v-else @click="runScan" :disabled="scanning"
                    class="w-full text-sm px-3 py-2.5 rounded-lg bg-orange-50 text-orange-700 border border-orange-200 hover:bg-orange-100">
              {{ scanning ? '🩺 体检中…' : '🩺 先做一次陈旧度体检' }}
            </button>

            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">额外要求（可选）</label>
              <textarea v-model="extraCtx" class="input-field text-sm h-16"
                        placeholder="例如：把案例换成 2025 年后的国内数据；补充多模态相关内容；语言更贴近本科生"></textarea>
            </div>

            <!-- 联动：更新依据也能来自原资料/题目/报告/项目对话/流水线/技能 -->
            <MaterialSourcePicker v-model="refreshSources" />
          </div>
          <div class="px-5 py-4 border-t border-surface-100 flex items-center justify-between">
            <span v-if="refreshMsg" class="text-xs" :class="refreshErr ? 'text-red-500' : 'text-green-600'">{{ refreshMsg }}</span>
            <div class="flex gap-2 ml-auto">
              <button @click="showRefresh = false" class="px-4 py-2 rounded-lg text-sm bg-surface-100 hover:bg-surface-200">关闭</button>
              <button @click="runRefresh" :disabled="refreshing || (!onlyRisky && !picked.length)"
                      class="px-4 py-2 rounded-lg text-sm bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-50">
                {{ refreshing ? '🤖 更新中（30~120s）…' : '✨ 生成 AI 更新版' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══ 版本链 ═══ -->
    <Teleport to="body">
      <div v-if="showVersions" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
           @click.self="showVersions = false">
        <div class="bg-white dark:bg-surface-900 rounded-xl shadow-2xl w-full max-w-md">
          <div class="px-5 py-4 border-b border-surface-100 flex items-center justify-between">
            <h3 class="font-semibold">🕘 版本链</h3>
            <button @click="showVersions = false" class="text-surface-400 hover:text-surface-600 text-xl leading-none">×</button>
          </div>
          <div class="p-4 space-y-2 max-h-[60vh] overflow-y-auto">
            <p v-if="!versions.length" class="text-sm text-surface-400 text-center py-6">暂无版本记录</p>
            <button v-for="v in versions" :key="v.id" @click="switchVersion(v.id)"
                    :class="['w-full text-left px-3 py-2.5 rounded-lg border transition-colors',
                             v.id === cwId ? 'border-primary-400 bg-primary-50' : 'border-surface-200 hover:bg-surface-50']">
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono px-1.5 py-0.5 rounded bg-surface-100">v{{ v.version }}</span>
                <span class="text-sm truncate flex-1">{{ v.title }}</span>
                <span v-if="v.id === cwId" class="text-[10px] text-primary-600">当前</span>
              </div>
              <p class="text-[11px] text-surface-500 mt-1">
                {{ v.source_type === 'ai_generated' ? '🤖 AI' : '📊 上传' }} · {{ v.slide_count }} 页 · {{ v.created_at?.slice(0, 10) }}
              </p>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { coursewareApi, type CoursewareDetail, type SlideMeta, type MaterialSelection } from '@/api/modules/courses'
import SlidePage from '@/components/course/SlidePage.vue'
import MaterialSourcePicker from '@/components/course/MaterialSourcePicker.vue'

const route = useRoute()
const router = useRouter()

const cwId = computed(() => Number(route.params.cwId || 0))
const courseId = computed(() => Number(route.params.courseId || 0))

const loading = ref(true)
const meta = reactive<CoursewareDetail>({
  id: 0, title: '', course_id: 0, course_title: '', cover_emoji: '📖', domain: '',
  course_project_id: null, version: 1, parent_id: null, source_type: 'upload', status: 'ready',
  slide_count: 0, file_size: 0, read_size_kb: 0, doc_id: null, is_teacher: false, enrolled: false,
  staleness: {}, optimization: {}, resume: null, slides: [],
})
const slides = computed(() => meta.slides)
const opt = computed(() => meta.optimization || {})
const current = ref(0)
const viewMode = ref<'slide' | 'book'>((localStorage.getItem('cw_read_view') as any) || 'slide')
const showNotes = ref(true)
const kw = ref('')
const readSet = ref<Set<number>>(new Set())

watch(viewMode, (v) => {
  localStorage.setItem('cw_read_view', v)
  if (v === 'book') nextTick(() => {
    const el = document.getElementById(`pg-${current.value}`)
    if (el) el.scrollIntoView({ block: 'start', behavior: 'smooth' })
  })
})

const tocList = computed(() => {
  const k = kw.value.toLowerCase()
  if (!k) return slides.value
  return slides.value.filter(s =>
    (s.title || '').toLowerCase().includes(k) ||
    (s.bullets || []).some(b => (b.text || '').toLowerCase().includes(k)) ||
    (s.notes || '').toLowerCase().includes(k))
})

const riskItems = computed(() => slides.value.filter(s => (s.risk_score || 0) >= 0.4))
const progressPct = computed(() => meta.slide_count ? Math.round(readSet.value.size / meta.slide_count * 100) : 0)

function fmtKB(kb: number) {
  if (!kb) return '0'
  return kb > 1024 ? (kb / 1024).toFixed(1) + ' MB' : Math.round(kb) + ' KB'
}

function onImgError(e: Event) {
  const el = e.target as HTMLImageElement
  if (el) el.style.display = 'none'
}

function jumpTo(i: number) {
  current.value = i
  if (viewMode.value === 'book') {
    nextTick(() => document.getElementById(`pg-${i}`)?.scrollIntoView({ block: 'start', behavior: 'smooth' }))
  } else {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  markRead(i)
}
function prev() { if (current.value > 0) jumpTo(current.value - 1) }
function next() { if (current.value < slides.value.length - 1) jumpTo(current.value + 1) }

// 读物模式滚动时同步目录高亮
function onBookScroll() {
  if (viewMode.value !== 'book') return
  for (const s of slides.value) {
    const el = document.getElementById(`pg-${s.slide_index}`)
    if (!el) continue
    const r = el.getBoundingClientRect()
    if (r.top <= 160 && r.bottom > 160) {
      if (current.value !== s.slide_index) { current.value = s.slide_index; markRead(s.slide_index) }
      break
    }
  }
}

let _reportTimer: any = null
function markRead(i: number) {
  if (!meta.enrolled) return
  if (readSet.value.has(i)) return
  readSet.value.add(i)
  readSet.value = new Set(readSet.value)
  clearTimeout(_reportTimer)
  _reportTimer = setTimeout(async () => {
    try {
      const res = await coursewareApi.reportProgress(cwId.value, i)
      void res
    } catch { /* ignore */ }
  }, 1500)
}

function goBack() { router.push(courseId.value ? `/course/${courseId.value}` : '/courses') }

// ═══ 删除课件 ═══
const deleting = ref(false)
async function removeThis() {
  if (!confirm(`确定删除《${meta.title}》？\n\n渲染图、导出缓存与派生文档会一并清理，且不可恢复。`)) return
  deleting.value = true
  try {
    await coursewareApi.remove(cwId.value)
    router.push(courseId.value ? `/course/${courseId.value}` : '/courses')
  } catch (e: any) {
    alert(e?.response?.data?.detail || '删除失败，请稍后重试')
  } finally {
    deleting.value = false
  }
}

function askThisSlide() {
  const s = slides.value[current.value]
  if (!s) return
  const body = [s.title, ...(s.bullets || []).map(b => b.text)].filter(Boolean).join('\n')
  const prefill = `关于《${meta.title}》第 ${s.slide_index + 1} 页：\n${body.slice(0, 600)}\n\n请出 3 道理解自测题并讲解易错点。`
  const pid = meta.course_project_id || ''
  const attach = meta.doc_id ? `&attachments=${meta.doc_id}` : ''
  router.push(`/chat?projectId=${pid}${attach}&prefill=${encodeURIComponent(prefill)}&courseId=${courseId.value}&cwId=${cwId.value}&slide=${s.slide_index}`)
}

// ═══ 陈旧度 + AI 更新 ═══
const showRefresh = ref(false)
const refreshing = ref(false)
const scanning = ref(false)
const refreshMsg = ref('')
const refreshErr = ref(false)
const onlyRisky = ref(true)
const picked = ref<number[]>([])
const extraCtx = ref('')
const refreshSources = ref<MaterialSelection>({})

function openRefresh() {
  showRefresh.value = true
  refreshMsg.value = ''
  picked.value = riskItems.value.map(s => s.slide_index)
  if (!riskItems.value.length) runScan()
}
function togglePick(i: number) {
  picked.value = picked.value.includes(i) ? picked.value.filter(x => x !== i) : [...picked.value, i]
}
function refreshOne(s: SlideMeta) {
  showRefresh.value = true
  onlyRisky.value = false
  picked.value = [s.slide_index]
}

async function runScan() {
  scanning.value = true
  try {
    await coursewareApi.stalenessScan(cwId.value)
    await loadDetail()
    picked.value = riskItems.value.map(s => s.slide_index)
  } catch (e: any) {
    refreshErr.value = true
    refreshMsg.value = e?.response?.data?.detail || '体检失败'
  } finally { scanning.value = false }
}

async function runRefresh() {
  refreshing.value = true
  refreshMsg.value = ''
  refreshErr.value = false
  try {
    const indexes = onlyRisky.value ? undefined : [...picked.value]
    const res = await coursewareApi.aiRefresh(cwId.value, {
      slide_indexes: indexes, extra_context: extraCtx.value, sources: refreshSources.value,
    })
    const d: any = res.data
    if (!d.new_courseware_id) {
      refreshMsg.value = d.message || '没有需要更新的页面'
      refreshErr.value = false
      return
    }
    refreshMsg.value = `✅ 已更新 ${d.updated} 页 → 新版本 v${d.version}（¥${(d.cost || 0).toFixed(4)}）` +
      (d.sources_used?.length ? ` · 引用 ${d.sources_used.length} 个素材源` : '')
    await new Promise(r => setTimeout(r, 900))
    showRefresh.value = false
    router.push(`/course/${courseId.value}/read/${d.new_courseware_id}`)
    await loadDetail()
  } catch (e: any) {
    refreshErr.value = true
    refreshMsg.value = e?.response?.data?.detail || '更新失败'
  } finally { refreshing.value = false }
}

// ═══ 版本 ═══
const showVersions = ref(false)
const versions = ref<any[]>([])
watch(showVersions, async (v) => {
  if (!v) return
  try { versions.value = (await coursewareApi.versions(cwId.value)).data.items || [] } catch { versions.value = [] }
})
function switchVersion(id: number) {
  showVersions.value = false
  router.push(`/course/${courseId.value}/read/${id}`)
}

async function loadDetail() {
  loading.value = true
  try {
    const res = await coursewareApi.detail(cwId.value)
    Object.assign(meta, res.data)
    const start = Number(route.query.slide || 0)
    current.value = Math.max(0, Math.min(slides.value.length - 1,
      start || (meta.resume?.courseware_id === meta.id ? meta.resume.slide_index : 0)))
    readSet.value = new Set([current.value])
    markRead(current.value)
  } catch (e: any) {
    console.error(e)
  } finally { loading.value = false }
}

function _key(e: KeyboardEvent) {
  const t = e.target as HTMLElement
  if (t && ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName)) return
  if (showRefresh.value || showVersions.value) return
  if (viewMode.value !== 'slide') return
  if (e.key === 'ArrowLeft') { e.preventDefault(); prev() }
  else if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); next() }
}

onMounted(async () => {
  await loadDetail()
  window.addEventListener('keydown', _key)
  window.addEventListener('scroll', onBookScroll, { passive: true })
})
watch(cwId, loadDetail)
onMounted(() => { /* keepalive */ })
</script>

<style scoped>
.scroll-mt-36 { scroll-margin-top: 9rem; }
</style>
