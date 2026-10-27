<template>
  <div class="max-w-6xl mx-auto px-5 py-7">
    <!-- 头部 -->
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-surface-900 flex items-center gap-2">
          <span>🌱</span>AI 通识课
        </h1>
        <p class="mt-1.5 text-sm text-surface-500">
          不用懂技术也能读。每节 6-8 分钟，读完知道 AI 是什么、哪里能信、怎么用得上。
        </p>
      </div>
      <button v-if="canCreate" class="btn-primary flex items-center gap-1.5" @click="openDraft">
        <span>✨</span>AI 帮我开一门课
      </button>
    </div>

    <!-- 筛选 -->
    <div class="mt-6 flex flex-wrap items-center gap-2">
      <div class="relative flex-1 min-w-[220px] max-w-sm">
        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-surface-400 text-sm">🔍</span>
        <input v-model="q" class="g-input w-full pl-9" placeholder="搜课程名、关键词，比如「提示词」" @keyup.enter="load" />
      </div>
      <select v-model="level" class="g-input" @change="load">
        <option value="">全部难度</option>
        <option value="零基础">零基础</option>
        <option value="进阶">进阶</option>
        <option value="专题">专题</option>
      </select>
      <button v-if="canCreate" :class="['px-3 py-2 rounded-lg text-sm border transition-colors',
              mine ? 'bg-primary-50 border-primary-300 text-primary-700' : 'border-surface-200 text-surface-600 hover:bg-surface-50']"
              @click="toggleMine">
        {{ mine ? '✓ 只看我建的' : '只看我建的' }}
      </button>
    </div>

    <!-- 分类 -->
    <div v-if="categories.length" class="mt-3 flex flex-wrap gap-2">
      <button :class="chipCls('')" @click="pickCategory('')">全部</button>
      <button v-for="c in categories" :key="c.name" :class="chipCls(c.name)" @click="pickCategory(c.name)">
        {{ c.name }}<span class="ml-1 opacity-60">{{ c.count }}</span>
      </button>
    </div>

    <!-- 列表 -->
    <div v-if="loading" class="mt-16 text-center text-sm text-surface-400">加载中…</div>

    <div v-else-if="!items.length" class="mt-12 rounded-2xl border border-dashed border-surface-300 bg-white px-6 py-16 text-center">
      <p class="text-3xl">🌾</p>
      <p class="mt-3 text-sm text-surface-600">{{ mine ? '你还没有创建课程' : '没有匹配的课程' }}</p>
      <p class="mt-1 text-xs text-surface-400">
        {{ canCreate ? '点右上角「AI 帮我开一门课」，输入一个主题就能生成大纲' : '换个关键词或分类试试' }}
      </p>
    </div>

    <div v-else class="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <router-link v-for="c in items" :key="c.id" :to="`/general/${c.id}`"
                   class="group bg-white rounded-2xl border border-surface-200 p-5 hover:border-primary-300 hover:shadow-md transition-all flex flex-col">
        <div class="flex items-start gap-3">
          <img v-if="c.cover_image && !coverFailed.has(c.id)"
               :src="generalCoverUrl(c.cover_image)" :alt="c.title"
               class="w-11 h-11 rounded-xl object-cover flex-shrink-0 border border-surface-100"
               @error="coverFailed.add(c.id)" />
          <div v-else class="w-11 h-11 rounded-xl bg-gradient-to-br from-primary-50 to-accent-50 flex items-center justify-center text-xl flex-shrink-0">
            {{ c.emoji || '🌱' }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-1.5">
              <h3 class="font-semibold text-surface-900 truncate group-hover:text-primary-700">{{ c.title }}</h3>
              <span v-if="c.status === 'draft'" class="g-badge-warn ml-1 flex-shrink-0">草稿</span>
            </div>
            <p class="mt-0.5 text-xs text-surface-400 truncate">{{ c.subtitle || c.category }}</p>
          </div>
        </div>

        <p class="mt-3 text-[13px] leading-relaxed text-surface-600 line-clamp-2">{{ c.summary || '还没有简介' }}</p>

        <div class="mt-3 flex flex-wrap gap-1.5">
          <span class="g-badge">{{ c.category }}</span>
          <span class="g-badge">{{ c.level }}</span>
          <span v-for="t in tagsOf(c)" :key="t" class="g-badge">{{ t }}</span>
        </div>

        <div class="mt-auto pt-4">
          <div class="flex items-center justify-between text-[11px] text-surface-400">
            <span>{{ c.ready_count || c.lesson_count }} 节 · 约 {{ c.minutes_total }} 分钟</span>
            <span v-if="c.done_count">{{ c.done_count }}/{{ c.ready_count }} 已学</span>
            <span v-else-if="c.ready_count">还没开始</span>
            <span v-else class="text-amber-600">待生成正文</span>
          </div>
          <div class="mt-2 h-1.5 rounded-full bg-surface-100 overflow-hidden">
            <div class="h-full bg-primary-500 transition-all" :style="{ width: percentOf(c) + '%' }"></div>
          </div>
        </div>
      </router-link>
    </div>

    <!-- AI 起草弹窗 -->
    <Teleport to="body">
      <div v-if="draftOpen" class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" @click.self="closeDraft">
        <div class="w-full max-w-lg bg-white rounded-2xl shadow-xl p-6 animate-slide-up">
          <div class="flex items-center justify-between">
            <h3 class="font-semibold text-surface-900">AI 帮我开一门课</h3>
            <button class="text-surface-400 hover:text-surface-600" @click="closeDraft">✕</button>
          </div>
          <p class="mt-1 text-xs text-surface-500">
            AI 先给出课程大纲和章节标题，你确认后可以逐节生成正文。正文也由 AI 写，你能随时改。
          </p>

          <div class="mt-5 space-y-4">
            <div>
              <label class="g-label">想讲什么主题？</label>
              <textarea v-model="form.topic" rows="3" class="g-input w-full resize-none"
                        placeholder="比如：给家里长辈讲清楚 AI 诈骗怎么防"></textarea>
              <p class="mt-1 text-[11px] text-surface-400">
                写具体一点效果更好：说明"讲给谁、解决什么问题"，比只写"AI 入门"有用得多。
              </p>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="g-label">讲给谁</label>
                <input v-model="form.audience" class="g-input w-full" placeholder="完全零基础的成年人" />
              </div>
              <div>
                <label class="g-label">难度</label>
                <select v-model="form.level" class="g-input w-full">
                  <option value="零基础">零基础</option>
                  <option value="进阶">进阶</option>
                  <option value="专题">专题</option>
                </select>
              </div>
            </div>
            <div>
              <label class="g-label">分几节（{{ form.chapter_count }} 节）</label>
              <input v-model.number="form.chapter_count" type="range" min="3" max="10" class="w-full accent-primary-600" />
              <p class="mt-1 text-[11px] text-surface-400">每节控制在 6-8 分钟能读完，不建议超过 10 节。</p>
            </div>
          </div>

          <p v-if="draftError" class="mt-4 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{{ draftError }}</p>

          <div class="mt-6 flex justify-end gap-2">
            <button class="btn-secondary" :disabled="drafting" @click="closeDraft">取消</button>
            <button class="btn-primary" :disabled="drafting || !form.topic.trim()" @click="submitDraft">
              {{ drafting ? 'AI 正在想大纲…' : '生成大纲' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { generalApi, generalCoverUrl, type GeneralCourseBrief } from '@/api/modules/general'
import './general.css'

const router = useRouter()

const items = ref<GeneralCourseBrief[]>([])
const categories = ref<{ name: string; count: number }[]>([])
const canCreate = ref(false)
const loading = ref(true)
const q = ref('')
const level = ref('')
const category = ref('')
const mine = ref(false)

const draftOpen = ref(false)
const drafting = ref(false)
const draftError = ref('')
const form = reactive({ topic: '', audience: '完全零基础的成年人', level: '零基础', chapter_count: 5 })

const coverFailed = reactive(new Set<number>())

/** 标签展示去重：排除与分类/难度重复的，最多 2 个 */
function tagsOf(c: GeneralCourseBrief): string[] {
  return (c.tags || []).filter(t => t !== c.category && t !== c.level).slice(0, 2)
}

function percentOf(c: GeneralCourseBrief) {
  if (!c.ready_count) return 0
  return Math.min(100, Math.round((c.done_count / c.ready_count) * 100))
}

function chipCls(name: string) {
  return ['px-3 py-1.5 rounded-full text-xs border transition-colors',
    category.value === name
      ? 'bg-primary-600 border-primary-600 text-white'
      : 'border-surface-200 text-surface-600 bg-white hover:border-primary-300 hover:text-primary-700']
}

async function load() {
  loading.value = true
  try {
    const r = await generalApi.list({
      q: q.value.trim(),
      category: category.value,
      level: level.value,
      mine: mine.value,
    })
    items.value = r.data.items || []
    categories.value = r.data.categories || []
    canCreate.value = !!r.data.can_create
  } catch (e: any) {
    items.value = []
  } finally {
    loading.value = false
  }
}

function pickCategory(name: string) {
  category.value = name
  load()
}

function toggleMine() {
  mine.value = !mine.value
  load()
}

function openDraft() {
  draftError.value = ''
  draftOpen.value = true
}

function closeDraft() {
  if (drafting.value) return
  draftOpen.value = false
}

async function submitDraft() {
  if (!form.topic.trim() || drafting.value) return
  drafting.value = true
  draftError.value = ''
  try {
    const r = await generalApi.draft({ ...form })
    draftOpen.value = false
    router.push(`/general/${r.data.course_id}`)
  } catch (e: any) {
    draftError.value = e?.response?.data?.detail || '生成失败，请稍后重试'
  } finally {
    drafting.value = false
  }
}

onMounted(load)
</script>
