<template>
  <div ref="rootEl" class="max-w-6xl mx-auto px-5 py-6">
    <div v-if="loading" class="py-24 text-center text-sm text-surface-400">加载中…</div>

    <div v-else-if="!lesson" class="py-24 text-center">
      <p class="text-sm text-surface-500">{{ error || '本节不存在' }}</p>
      <router-link to="/general" class="btn-secondary mt-4 inline-block">返回课程广场</router-link>
    </div>

    <template v-else>
      <!-- 顶部：面包屑 + 阅读进度 + 完成状态 -->
      <div class="flex flex-wrap items-center justify-between gap-3">
        <router-link :to="`/general/${lesson.course_id}`"
                     class="text-xs text-surface-400 hover:text-primary-600 truncate">
          ← {{ lesson.course_title }}
        </router-link>
        <div class="flex items-center gap-3">
          <span class="text-[11px] text-surface-400">第 {{ lesson.index }} / {{ lesson.total }} 节</span>
          <span class="text-[11px] text-surface-400">已读 {{ readPct }}%</span>
          <span v-if="lesson.done" class="g-badge-ok">✓ 已学完</span>
          <button v-else class="btn-primary text-xs" :disabled="marking" @click="markDone">
            {{ marking ? '保存中…' : '✓ 标记学完' }}
          </button>
        </div>
      </div>
      <div class="mt-2 h-1 rounded-full bg-surface-200 overflow-hidden">
        <div class="h-full bg-primary-500 transition-all" :style="{ width: readPct + '%' }"></div>
      </div>

      <div class="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_330px]">
        <!-- 正文 -->
        <article class="rounded-2xl border border-surface-200 bg-white p-6 sm:p-8">
          <img v-if="lesson.cover_image && coverOk"
               :src="generalCoverUrl(lesson.cover_image)" :alt="lesson.title"
               class="mb-5 w-full max-h-72 object-cover rounded-xl border border-surface-100"
               @error="coverOk = false" />
          <p v-if="lesson.kicker" class="text-[11px] tracking-widest text-primary-600">{{ lesson.kicker }}</p>
          <h1 class="mt-2 text-2xl font-bold leading-snug text-surface-900">{{ lesson.title }}</h1>
          <div class="mt-2 flex items-center gap-2 text-[11px] text-surface-400">
            <span>约 {{ lesson.minutes }} 分钟读完</span>
            <span v-if="lesson.summary">·</span>
            <span class="line-clamp-1">{{ lesson.summary }}</span>
          </div>
          <div class="my-6 h-px bg-surface-100"></div>

          <!-- 图解块：正文前的可视化小结 -->
          <div v-if="lesson.figure && lesson.figure.length" class="mb-6 space-y-3">
            <LessonFigure v-for="(f, i) in lesson.figure" :key="i" :block="f" />
          </div>

          <div class="g-read">
            <MarkdownView :content="lesson.content" />
          </div>

          <!-- 读完 -->
          <div class="mt-10 rounded-xl border border-surface-200 bg-surface-50 p-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p class="text-sm font-medium text-surface-800">
                  {{ lesson.done ? '这一节你已经学完了' : '这一节读完了吗？' }}
                </p>
                <p class="mt-0.5 text-[11px] text-surface-500">
                  标记完成后，课程进度会记住，下次回来直接跳到没读的那一节。
                </p>
              </div>
              <div class="flex items-center gap-2">
                <button v-if="lesson.prev_id" class="btn-secondary text-xs" @click="go(lesson.prev_id)">
                  ← 上一节
                </button>
                <button v-if="!lesson.done" class="btn-primary text-xs" :disabled="marking" @click="markDone">
                  标记学完
                </button>
                <button v-if="lesson.next_id" class="btn-secondary text-xs" @click="go(lesson.next_id)">
                  下一节 →
                </button>
              </div>
            </div>
            <p v-if="progressNote" class="mt-3 rounded-lg bg-accent-50 px-3 py-2 text-[11px] text-accent-700">
              {{ progressNote }}
            </p>
          </div>
        </article>

        <!-- 右栏：自身可滚动，避免长内容超出视口点不到助教 -->
        <aside class="space-y-4 lg:sticky lg:top-2 lg:self-start lg:max-h-[calc(100vh-2rem)] lg:overflow-y-auto lg:pr-1">
          <!-- 随堂自测 -->
          <div v-if="lesson.quiz.length" class="rounded-2xl border border-surface-200 bg-white p-5">
            <div class="flex items-center justify-between">
              <h2 class="text-sm font-semibold text-surface-800">📝 随堂自测</h2>
              <span class="text-[11px] text-surface-400">{{ answeredCount }}/{{ lesson.quiz.length }}</span>
            </div>
            <p class="mt-1 text-[11px] text-surface-400">选一个答案，立刻知道对不对——错了也不扣分。</p>

            <div class="mt-4 space-y-5">
              <div v-for="(item, qi) in lesson.quiz" :key="qi">
                <p class="text-[13px] font-medium leading-relaxed text-surface-800">
                  {{ qi + 1 }}. {{ item.q }}
                </p>
                <div class="mt-2 space-y-1.5">
                  <button v-for="(opt, oi) in item.options" :key="oi"
                          class="w-full text-left px-3 py-2 rounded-lg border text-[12.5px] leading-snug transition-colors"
                          :class="optionCls(qi, oi, item.answer)"
                          :disabled="answers[qi] !== undefined"
                          @click="answer(qi, oi)">
                    <span class="font-medium mr-1.5">{{ 'ABCD'[oi] }}</span>{{ opt }}
                  </button>
                </div>
                <p v-if="answers[qi] !== undefined"
                   class="mt-2 rounded-lg px-3 py-2 text-[11.5px] leading-relaxed"
                   :class="answers[qi] === item.answer ? 'bg-accent-50 text-accent-700' : 'bg-amber-50 text-amber-700'">
                  {{ answers[qi] === item.answer ? '✓ 答对了。' : `✗ 正确答案是 ${'ABCD'[item.answer]}。` }}{{ item.explain }}
                </p>
              </div>
            </div>

            <p v-if="answeredCount === lesson.quiz.length"
               class="mt-4 rounded-lg bg-primary-50 px-3 py-2 text-[11.5px] text-primary-700">
              全部答完，答对 {{ correctCount }} 题。{{ correctCount === lesson.quiz.length ? '概念已经清楚了，可以继续下一节。' : '错的那题建议回上面再看一眼那一段。' }}
            </p>
          </div>

          <!-- AI 助教 -->
          <div class="rounded-2xl border border-surface-200 bg-white p-5">
            <h2 class="text-sm font-semibold text-surface-800">🤖 AI 助教</h2>
            <p class="mt-1 text-[11px] text-surface-400">只依据本节内容回答，不会跨课瞎编。</p>

            <div v-if="chat.length" class="mt-3 max-h-72 space-y-2.5 overflow-y-auto pr-1">
              <div v-for="(m, i) in chat" :key="i" class="text-[12.5px] leading-relaxed"
                   :class="m.role === 'user' ? 'text-right' : ''">
                <span class="inline-block px-3 py-2 rounded-xl text-left"
                      :class="m.role === 'user' ? 'bg-primary-600 text-white' : 'bg-surface-100 text-surface-700'">
                  {{ m.text }}
                </span>
              </div>
              <p v-if="asking" class="text-[12px] text-surface-400">助教正在想…</p>
            </div>

            <div class="mt-3 flex flex-wrap gap-1.5">
              <button v-for="s in suggestions" :key="s" class="g-badge hover:bg-primary-50 hover:text-primary-700"
                      @click="ask(s)">
                {{ s }}
              </button>
            </div>

            <div class="mt-2.5 flex items-center gap-2">
              <input v-model="question" class="g-input flex-1" placeholder="这一节哪里没看懂？"
                     :disabled="asking" @keyup.enter="ask()" />
              <button class="btn-primary text-xs" :disabled="asking || !question.trim()" @click="ask()">问</button>
            </div>
            <p v-if="askError" class="mt-2 text-[11px] text-red-600">{{ askError }}</p>
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownView from '@/components/common/MarkdownView.vue'
import LessonFigure from './LessonFigure.vue'
import { generalApi, generalCoverUrl, type GeneralLessonDetail } from '@/api/modules/general'
import './general.css'

const route = useRoute()
const router = useRouter()

const rootEl = ref<HTMLElement | null>(null)
const lesson = ref<GeneralLessonDetail | null>(null)
const loading = ref(true)
const error = ref('')

const answers = ref<Record<number, number>>({})
const question = ref('')
const asking = ref(false)
const askError = ref('')
const chat = ref<{ role: 'user' | 'ai'; text: string }[]>([])
const marking = ref(false)
const progressNote = ref('')
const readPct = ref(0)
const coverOk = ref(true)

const suggestions = ['用一句话再说一遍', '举个生活里的例子', '这跟我有什么关系']

const answeredCount = computed(() => Object.keys(answers.value).length)
const correctCount = computed(() => {
  if (!lesson.value) return 0
  return lesson.value.quiz.reduce((n, q, i) => n + (answers.value[i] === q.answer ? 1 : 0), 0)
})

function optionCls(qi: number, oi: number, right: number) {
  const picked = answers.value[qi]
  if (picked === undefined) {
    return 'border-surface-200 text-surface-600 hover:border-primary-300 hover:bg-primary-50'
  }
  if (oi === right) return 'border-accent-300 bg-accent-50 text-accent-800'
  if (oi === picked) return 'border-red-300 bg-red-50 text-red-700'
  return 'border-surface-200 text-surface-400'
}

function answer(qi: number, oi: number) {
  if (answers.value[qi] !== undefined) return
  answers.value = { ...answers.value, [qi]: oi }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const r = await generalApi.lesson(Number(route.params.lid))
    lesson.value = r.data
    coverOk.value = true
    answers.value = {}
    chat.value = []
  } catch (e: any) {
    lesson.value = null
    error.value = e?.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

/** main 是外层滚动容器，往上找到第一个可滚动祖先 */
function findScroller(el: HTMLElement | null): HTMLElement | null {
  let node = el?.parentElement ?? null
  while (node) {
    const oy = getComputedStyle(node).overflowY
    if ((oy === 'auto' || oy === 'scroll') && node.scrollHeight > node.clientHeight) return node
    node = node.parentElement
  }
  return null
}

let scroller: HTMLElement | null = null
let lastReported = 0
let reportTimer: any = null

function onScroll() {
  const box = scroller
  if (!box) return
  const max = box.scrollHeight - box.clientHeight
  const pct = max > 0 ? Math.min(100, Math.round((box.scrollTop / max) * 100)) : 100
  // 已读%只增不减，回看时不回落
  if (pct > readPct.value) readPct.value = pct
  // 读满 80% 才自动上报，且只在进度前进 20% 以上时报一次，避免频繁写库
  if (!lesson.value || lesson.value.done) return
  if (pct < 80 || pct - lastReported < 20) return
  lastReported = pct
  clearTimeout(reportTimer)
  reportTimer = setTimeout(() => {
    generalApi.progress(lesson.value!.id, { percent: Math.min(95, pct) }).catch(() => {})
  }, 800)
}

async function markDone() {
  if (!lesson.value || marking.value) return
  marking.value = true
  progressNote.value = ''
  try {
    const r = await generalApi.progress(lesson.value.id, { done: true })
    lesson.value.done = true
    progressNote.value = `已记录。这门课你已完成 ${r.data.done_count}/${r.data.ready_count} 节（${r.data.course_percent}%）。`
  } catch (e: any) {
    progressNote.value = e?.response?.data?.detail || '保存失败，请重试'
  } finally {
    marking.value = false
  }
}

function go(id: number | null) {
  if (id) router.push(`/general/lesson/${id}`)
}

async function ask(text?: string) {
  const q = (text ?? question.value).trim()
  if (!q || asking.value || !lesson.value) return
  chat.value.push({ role: 'user', text: q })
  question.value = ''
  asking.value = true
  askError.value = ''
  try {
    const r = await generalApi.ask(lesson.value.id, q)
    chat.value.push({ role: 'ai', text: r.data.answer })
  } catch (e: any) {
    askError.value = e?.response?.data?.detail || '助教暂时不可用，请稍后重试'
  } finally {
    asking.value = false
  }
}

onMounted(async () => {
  await load()
  scroller = findScroller(rootEl.value)
  scroller?.addEventListener('scroll', onScroll, { passive: true })
})

onUnmounted(() => {
  scroller?.removeEventListener('scroll', onScroll)
  clearTimeout(reportTimer)
})
</script>
