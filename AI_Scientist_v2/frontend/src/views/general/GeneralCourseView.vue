<template>
  <div class="max-w-5xl mx-auto px-5 py-7">
    <div v-if="loading" class="py-24 text-center text-sm text-surface-400">加载中…</div>

    <div v-else-if="!course" class="py-24 text-center">
      <p class="text-sm text-surface-500">{{ error || '课程不存在' }}</p>
      <router-link to="/general" class="btn-secondary mt-4 inline-block">返回课程广场</router-link>
    </div>

    <template v-else>
      <!-- 返回 -->
      <router-link to="/general" class="text-xs text-surface-400 hover:text-primary-600">← 课程广场</router-link>

      <!-- 封面 -->
      <div class="mt-4 rounded-2xl border border-surface-200 bg-white overflow-hidden">
        <div class="h-1.5 bg-gradient-to-r from-primary-500 via-primary-400 to-accent-400"></div>
        <img v-if="course.cover_image && coverOk"
             :src="generalCoverUrl(course.cover_image)" :alt="course.title"
             class="w-full max-h-64 object-cover"
             @error="coverOk = false" />
        <div class="p-6">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div class="flex items-start gap-4 min-w-0">
              <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-50 to-accent-50 flex items-center justify-center text-2xl flex-shrink-0">
                {{ course.emoji || '🌱' }}
              </div>
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <h1 class="text-xl font-bold text-surface-900">{{ course.title }}</h1>
                  <span v-if="course.status === 'draft'" class="g-badge-warn">草稿 · 仅你可见</span>
                </div>
                <p class="mt-1 text-sm text-surface-500">{{ course.subtitle }}</p>
                <div class="mt-2 flex flex-wrap items-center gap-1.5">
                  <span class="g-badge">{{ course.category }}</span>
                  <span class="g-badge">{{ course.level }}</span>
                  <span class="g-badge">{{ course.ready_count }} 节 · 约 {{ course.minutes_total }} 分钟</span>
                  <span v-for="t in tagsShown" :key="t" class="g-badge">{{ t }}</span>
                </div>
              </div>
            </div>

            <div class="flex flex-col items-end gap-2">
              <router-link v-if="course.next_lesson_id" :to="`/general/lesson/${course.next_lesson_id}`"
                           class="btn-primary whitespace-nowrap">
                {{ course.done_count ? '继续学习' : '开始学习' }}
              </router-link>
              <p class="text-[11px] text-surface-400">
                已完成 {{ course.done_count }}/{{ course.ready_count }} 节
              </p>
            </div>
          </div>

          <p class="mt-4 text-sm leading-relaxed text-surface-600">{{ course.summary }}</p>

          <div class="mt-4 h-2 rounded-full bg-surface-100 overflow-hidden">
            <div class="h-full bg-primary-500 transition-all" :style="{ width: percent + '%' }"></div>
          </div>
        </div>
      </div>

      <!-- 教师工具栏 -->
      <div v-if="course.is_owner" class="mt-4 rounded-xl border border-primary-100 bg-primary-50/60 p-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-sm font-medium text-surface-800">作者工具</p>
            <p class="mt-0.5 text-[11px] text-surface-500">
              正文由 AI 逐节生成，每节约 10-20 秒。可以先挑一节看效果，满意了再批量生成。
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button class="btn-secondary text-xs" :disabled="batch.running || !pendingCount"
                    @click="genAll">
              {{ batch.running ? `生成中 ${batch.done}/${batch.total}…` : `⚡ 生成未完成的 ${pendingCount} 节` }}
            </button>
            <button v-if="batch.running" class="btn-secondary text-xs" @click="batch.running = false">停止</button>
            <button v-if="course.status !== 'published'" class="btn-primary text-xs"
                    :disabled="!course.ready_count" @click="publish">
              发布课程
            </button>
            <button class="btn-secondary text-xs" :disabled="course.status === 'published'" @click="publish"
                    v-if="course.status === 'published'">
              ✓ 已发布
            </button>
            <button class="px-3 py-2 rounded-lg text-xs text-red-600 border border-red-200 hover:bg-red-50"
                    @click="remove">删除</button>
          </div>
        </div>
        <p v-if="batch.error" class="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{{ batch.error }}</p>
        <p v-if="notice" class="mt-3 rounded-lg bg-accent-50 px-3 py-2 text-xs text-accent-700">{{ notice }}</p>
      </div>

      <!-- 目录 -->
      <div class="mt-6">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-semibold text-surface-800">课程目录</h2>
          <span class="text-[11px] text-surface-400">按顺序读，每节独立成篇</span>
        </div>

        <div class="mt-3 space-y-2">
          <div v-for="(l, i) in course.lessons" :key="l.id"
               class="group rounded-xl border transition-all"
               :class="l.status === 'ready'
                 ? 'bg-white border-surface-200 hover:border-primary-300 hover:shadow-sm'
                 : 'bg-surface-50 border-dashed border-surface-300'">
            <div class="flex items-center gap-3 p-4">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center text-[11px] font-semibold flex-shrink-0"
                   :class="l.done ? 'bg-accent-100 text-accent-700' : 'bg-surface-100 text-surface-500'">
                {{ l.done ? '✓' : String(i + 1).padStart(2, '0') }}
              </div>

              <router-link v-if="l.status === 'ready'" :to="`/general/lesson/${l.id}`" class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <p class="font-medium text-surface-900 truncate group-hover:text-primary-700">{{ l.title }}</p>
                  <span v-if="l.done" class="g-badge-ok flex-shrink-0">已学完</span>
                </div>
                <p class="mt-0.5 text-xs text-surface-500 truncate">{{ l.kicker }} · {{ l.summary }}</p>
              </router-link>

              <div v-else class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <p class="font-medium text-surface-500 truncate">{{ l.title }}</p>
                  <span class="g-badge-warn flex-shrink-0">待生成</span>
                </div>
                <p class="mt-0.5 text-xs text-surface-400 truncate">{{ l.kicker }} · {{ l.summary || '正文还没生成' }}</p>
              </div>

              <div class="flex items-center gap-2 flex-shrink-0">
                <span class="text-[11px] text-surface-400 hidden sm:inline">{{ l.minutes }} 分钟</span>
                <button v-if="course.is_owner" class="text-[11px] px-2.5 py-1.5 rounded-md border border-surface-200 text-surface-600 hover:border-primary-300 hover:text-primary-700 disabled:opacity-50"
                        :disabled="genState[l.id] === 'running' || batch.running"
                        @click="genOne(l.id)">
                  {{ genState[l.id] === 'running' ? '生成中…' : (l.status === 'ready' ? '重生成' : '生成本节') }}
                </button>
                <span v-if="genState[l.id] === 'error'" class="text-[11px] text-red-600">失败</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 知识图谱（可折叠） -->
      <div class="mt-6">
        <button class="w-full flex items-center justify-between text-sm font-semibold text-surface-800"
                @click="graphOpen = !graphOpen">
          <span>🕸️ 知识图谱</span>
          <span class="text-[11px] text-surface-400">{{ graphOpen ? '收起 ▲' : '展开 ▼' }}</span>
        </button>
        <div v-if="graphOpen" class="mt-3" style="height: 420px">
          <GraphView scope="general" :scope-id="course.id"
                     empty-tip="让 AI 从课程大纲抽取知识图谱" />
        </div>
      </div>

      <p class="mt-8 text-center text-[11px] text-surface-400">
        本文由 AI 生成初稿，作者可逐节重写。读到不对的地方，随时用每节底部的 AI 助教追问。
      </p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import GraphView from '@/components/common/GraphView.vue'
import { generalApi, generalCoverUrl, type GeneralCourseDetail } from '@/api/modules/general'
import './general.css'

const graphOpen = ref(false)

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const course = ref<GeneralCourseDetail | null>(null)
const loading = ref(true)
const error = ref('')
const notice = ref('')
const coverOk = ref(true)
const genState = reactive<Record<number, 'idle' | 'running' | 'error'>>({})
const batch = reactive({ running: false, done: 0, total: 0, error: '' })

const courseId = computed(() => Number(route.params.id))
const percent = computed(() => {
  const c = course.value
  if (!c || !c.ready_count) return 0
  return Math.min(100, Math.round((c.done_count / c.ready_count) * 100))
})
const pendingCount = computed(() => (course.value?.lessons || []).filter(l => l.status !== 'ready').length)

/** 标签展示去重：排除与分类/难度重复的 */
const tagsShown = computed(() => {
  const c = course.value
  if (!c) return []
  return (c.tags || []).filter(t => t !== c.category && t !== c.level)
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const r = await generalApi.detail(courseId.value)
    course.value = r.data
  } catch (e: any) {
    course.value = null
    error.value = e?.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

async function genOne(id: number) {
  genState[id] = 'running'
  try {
    const r = await generalApi.generateLesson(id, { mode: appStore.mode, model: appStore.preferredModel || undefined })
    genState[id] = 'idle'
    if (r.data.fallback_from) {
      notice.value = `所选模型 ${r.data.fallback_from} 当前不可用，已自动改用 ${r.data.model} 完成。`
    }
    await load()
  } catch (e: any) {
    genState[id] = 'error'
    throw e
  }
}

async function genAll() {
  const todo = (course.value?.lessons || []).filter(l => l.status !== 'ready').map(l => l.id)
  if (!todo.length) return
  batch.running = true
  batch.total = todo.length
  batch.done = 0
  batch.error = ''
  notice.value = ''
  const failed: number[] = []
  for (const id of todo) {
    if (!batch.running) break
    try {
      await genOne(id)
      batch.done++
    } catch (e: any) {
      // 单节失败不打断整批：之前一遇错就 break，剩下的节永远停在 pending
      failed.push(id)
      batch.error = `已有 ${failed.length} 节失败（多为模型限流/超时），其余继续生成中…`
    }
  }
  batch.running = false
  await load()
  if (failed.length) {
    batch.error = `本次有 ${failed.length} 节没生成成功（大多是模型限流或超时），其余已完成；可再点一次本按钮补生成`
  }
}

async function publish() {
  try {
    await generalApi.publish(courseId.value)
    notice.value = '课程已发布，所有登录用户都能在课程广场看到它。'
    await load()
  } catch (e: any) {
    batch.error = e?.response?.data?.detail || '发布失败'
  }
}

async function remove() {
  if (!window.confirm('删除后这门课和所有章节内容都会消失，确定吗？')) return
  try {
    await generalApi.remove(courseId.value)
    router.replace('/general')
  } catch (e: any) {
    batch.error = e?.response?.data?.detail || '删除失败'
  }
}

onMounted(load)
</script>
