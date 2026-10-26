<template>
  <div v-if="slide" class="card overflow-hidden">
    <!-- 陈旧度提示条 -->
    <div v-if="slide.risk_score >= 0.4" class="px-4 py-2.5 bg-orange-50 border-b border-orange-100 flex items-start gap-2">
      <span class="text-sm flex-shrink-0">⚠️</span>
      <div class="min-w-0 flex-1">
        <p class="text-xs text-orange-800 font-medium">
          AI 判断此页可能过时
          <span v-if="slide.risk_category" class="ml-1 px-1.5 py-0.5 rounded bg-orange-100 text-[10px]">{{ slide.risk_category }}</span>
          <span class="ml-1 text-orange-500">风险 {{ (slide.risk_score * 100).toFixed(0) }}%</span>
        </p>
        <p v-if="slide.ai_reason" class="text-[11px] text-orange-600 mt-0.5">{{ slide.ai_reason }}</p>
        <p v-if="slide.ai_suggestion" class="text-[11px] text-orange-700 mt-0.5">💡 {{ slide.ai_suggestion }}</p>
      </div>
    </div>
    <div v-else-if="slide.updated_by_ai" class="px-4 py-2 bg-purple-50 border-b border-purple-100 text-[11px] text-purple-700">
      ✨ 此页已由 AI 更新（原版本保留在版本链中）
    </div>

    <!-- ═══ 幻灯片主体：按 layout 渲染，和导出的 pptx 同一套版式 ═══ -->
    <div :class="['relative', isDark ? 'bg-slate-900' : 'bg-white']">
      <div v-if="isDark" class="absolute left-0 top-0 bottom-0 w-1.5 bg-indigo-400/70"></div>

      <div class="px-6 py-7 md:px-10 md:py-9 min-h-[320px] flex flex-col">
        <!-- 封面 -->
        <template v-if="layout === 'cover'">
          <p class="text-xs md:text-sm text-indigo-300 tracking-wide">{{ slide.kicker }}</p>
          <h1 class="mt-4 text-2xl md:text-[34px] font-bold leading-snug text-white">{{ slide.title }}</h1>
          <div class="mt-5 h-1 w-24 rounded bg-indigo-400"></div>
          <p v-if="slide.lead" class="mt-auto pt-10 text-sm text-slate-400">{{ slide.lead }}</p>
        </template>

        <!-- 章节过渡页 -->
        <template v-else-if="layout === 'section'">
          <span class="text-6xl md:text-[76px] font-bold text-indigo-100 leading-none">{{ chapterNo }}</span>
          <h2 class="mt-3 text-2xl md:text-3xl font-bold text-surface-900">{{ slide.chapter || slide.title }}</h2>
          <div class="mt-3 h-0.5 w-12 bg-indigo-400"></div>
          <template v-if="slide.key_question">
            <p class="mt-4 text-[11px] font-semibold text-indigo-600">本章要解决</p>
            <p class="mt-1 text-base md:text-lg text-surface-600 leading-relaxed">{{ slide.key_question }}</p>
          </template>
        </template>

        <!-- 结课页 -->
        <template v-else-if="layout === 'end'">
          <p class="text-xs text-indigo-300">结课</p>
          <h2 class="mt-2 text-3xl md:text-4xl font-bold text-white">{{ slide.title || '谢谢' }}</h2>
          <div class="mt-4 h-1 w-20 rounded bg-indigo-400"></div>
          <ol class="mt-8 space-y-3">
            <li v-for="(t, i) in (slide.takeaway || [])" :key="i" class="flex items-start gap-3">
              <span class="text-[11px] font-bold text-indigo-300 mt-1">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="text-sm md:text-base text-slate-200 leading-relaxed">{{ t }}</span>
            </li>
          </ol>
        </template>

        <!-- 内容页 -->
        <template v-else>
          <div v-if="slide.kicker" class="flex items-center gap-2">
            <span class="h-0.5 w-6 bg-indigo-600"></span>
            <span class="text-[11px] font-semibold text-indigo-600 tracking-wide">{{ slide.kicker }}</span>
          </div>
          <h2 class="mt-2 text-xl md:text-[26px] font-bold leading-snug text-surface-900">{{ slide.title || '（无标题页）' }}</h2>
          <p v-if="slide.lead" class="mt-1.5 text-sm text-surface-500 leading-relaxed">{{ slide.lead }}</p>
          <div class="mt-4 h-px bg-surface-200"></div>

          <div class="mt-5 flex-1">
            <!-- 要点 + 「讲透这一页」侧栏 -->
            <div v-if="layout === 'bullets'"
                 :class="slide.detail || slide.example ? 'grid gap-4 md:grid-cols-5' : ''">
              <ul class="space-y-4" :class="slide.detail || slide.example ? 'md:col-span-3' : ''">
                <li v-for="(b, i) in bulletRows" :key="i"
                    :class="[b.level >= 1 ? 'ml-8' : '', 'flex items-start gap-3']">
                  <span v-if="b.level >= 1" class="mt-2.5 h-0.5 w-3 bg-indigo-300 flex-shrink-0"></span>
                  <span v-else
                        class="mt-0.5 h-7 w-7 flex-shrink-0 rounded-lg bg-indigo-50 text-indigo-600 text-xs font-bold flex items-center justify-center">
                    {{ b.num }}
                  </span>
                  <span :class="[b.level >= 1 ? 'text-sm text-surface-600' : 'text-[15px] md:text-base text-surface-800 font-medium', 'leading-relaxed pt-1']">
                    {{ b.text }}
                  </span>
                </li>
              </ul>
              <div v-if="slide.detail || slide.example" class="md:col-span-2 rounded-xl bg-surface-50 p-4">
                <p class="text-[11px] font-semibold text-indigo-600">讲透这一页</p>
                <p v-if="slide.detail" class="mt-2 text-xs text-surface-700 leading-relaxed">{{ slide.detail }}</p>
                <div v-if="slide.example" class="mt-3 rounded-lg bg-amber-50 p-3">
                  <p class="text-[10px] font-semibold text-amber-700">案例 / 例题</p>
                  <p class="mt-1 text-xs text-amber-900 leading-relaxed">{{ slide.example }}</p>
                </div>
              </div>
            </div>

            <!-- 数据图：柱状 / 条形 / 折线 -->
            <div v-else-if="layout === 'chart' && slide.chart" class="space-y-3">
              <div v-if="slide.chart.type === 'line'" class="rounded-xl bg-surface-50 p-3">
                <svg viewBox="0 0 100 46" preserveAspectRatio="none" class="w-full h-48">
                  <polyline :points="linePoints" fill="none" stroke="#4338CA" stroke-width="1.4" />
                  <circle v-for="(p, i) in lineDots" :key="i" :cx="p.x" :cy="p.y" r="1.4"
                          fill="#fff" stroke="#4338CA" stroke-width="1" />
                </svg>
                <div class="mt-1 flex text-[10px] text-surface-500">
                  <span v-for="(l, i) in slide.chart.labels" :key="i" class="flex-1 text-center truncate">{{ l }}</span>
                </div>
              </div>

              <div v-else-if="slide.chart.type === 'hbar'" class="space-y-3 rounded-xl bg-surface-50 p-4">
                <div v-for="(b, i) in chartBars" :key="i" class="space-y-1">
                  <div class="flex items-baseline justify-between text-[11px]">
                    <span class="text-surface-700">{{ b.label }}</span>
                    <span class="font-semibold" :class="b.hot ? 'text-cyan-700' : 'text-indigo-700'">
                      {{ b.value }}{{ slide.chart.unit || '' }}
                    </span>
                  </div>
                  <div class="h-2.5 rounded bg-white">
                    <div class="h-2.5 rounded" :class="b.hot ? 'bg-cyan-600' : 'bg-indigo-600'"
                         :style="{ width: b.pct + '%' }"></div>
                  </div>
                </div>
              </div>

              <div v-else class="rounded-xl bg-surface-50 px-4 pt-4 pb-2">
                <div class="flex h-48 items-end gap-3">
                  <div v-for="(b, i) in chartBars" :key="i" class="flex-1 flex flex-col items-center justify-end h-full">
                    <span class="mb-1 text-[10px] font-semibold" :class="b.hot ? 'text-cyan-700' : 'text-indigo-700'">
                      {{ b.value }}{{ slide.chart.unit || '' }}
                    </span>
                    <div class="w-full max-w-[54px] rounded-t-md" :class="b.hot ? 'bg-cyan-600' : 'bg-indigo-600'"
                         :style="{ height: b.pct + '%' }"></div>
                    <span class="mt-1.5 w-full truncate text-center text-[10px] text-surface-500">{{ b.label }}</span>
                  </div>
                </div>
              </div>
              <p v-if="slide.chart.caption" class="text-[10px] text-surface-400">数据来源：{{ slide.chart.caption }}</p>
              <p v-if="slide.detail" class="text-xs text-surface-600 leading-relaxed">{{ slide.detail }}</p>
            </div>

            <!-- 流程 / 机制图 -->
            <div v-else-if="layout === 'flow'" class="space-y-3">
              <div v-for="(s, i) in (slide.steps || [])" :key="i" class="flex gap-3">
                <div class="flex flex-col items-center">
                  <span class="h-7 w-7 shrink-0 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">
                    {{ i + 1 }}
                  </span>
                  <span v-if="i < (slide.steps || []).length - 1" class="mt-1 w-px flex-1 bg-indigo-200"></span>
                </div>
                <div class="pb-3">
                  <p class="text-sm font-bold text-surface-900">{{ s.title }}</p>
                  <p v-if="s.desc" class="mt-0.5 text-xs text-surface-600 leading-relaxed">{{ s.desc }}</p>
                </div>
              </div>
              <p v-if="slide.detail" class="text-xs text-surface-600 leading-relaxed">{{ slide.detail }}</p>
            </div>

            <!-- 图文分栏：左论点 + 右图 -->
            <div v-else-if="layout === 'split'" class="grid gap-4 md:grid-cols-2">
              <ul class="space-y-3">
                <li v-for="(b, i) in bulletRows" :key="i"
                    :class="[b.level >= 1 ? 'ml-7' : '', 'flex items-start gap-2.5']">
                  <span v-if="b.level >= 1" class="mt-2 h-0.5 w-3 bg-indigo-300 flex-shrink-0"></span>
                  <span v-else
                        class="mt-0.5 h-6 w-6 flex-shrink-0 rounded-lg bg-indigo-50 text-indigo-600 text-[11px] font-bold flex items-center justify-center">
                    {{ b.num }}
                  </span>
                  <span :class="[b.level >= 1 ? 'text-xs text-surface-600' : 'text-sm text-surface-800 font-medium', 'leading-relaxed']">
                    {{ b.text }}
                  </span>
                </li>
              </ul>
              <div class="space-y-2">
                <div v-if="slide.chart" class="space-y-2 rounded-xl bg-surface-50 p-3.5">
                  <div v-for="(b, i) in chartBars" :key="i" class="space-y-1">
                    <div class="flex items-baseline justify-between text-[11px]">
                      <span class="text-surface-700">{{ b.label }}</span>
                      <span class="font-semibold" :class="b.hot ? 'text-cyan-700' : 'text-indigo-700'">
                        {{ b.value }}{{ slide.chart.unit || '' }}
                      </span>
                    </div>
                    <div class="h-2 rounded bg-white">
                      <div class="h-2 rounded" :class="b.hot ? 'bg-cyan-600' : 'bg-indigo-600'"
                           :style="{ width: b.pct + '%' }"></div>
                    </div>
                  </div>
                </div>
                <ol v-else-if="slide.steps" class="space-y-2">
                  <li v-for="(s, i) in slide.steps" :key="i" class="flex gap-2.5 rounded-lg bg-surface-50 p-2.5">
                    <span class="h-5 w-5 shrink-0 rounded-full bg-indigo-600 text-white text-[10px] font-bold flex items-center justify-center">
                      {{ i + 1 }}
                    </span>
                    <div class="min-w-0">
                      <p class="text-xs font-semibold text-surface-800">{{ s.title }}</p>
                      <p v-if="s.desc" class="mt-0.5 text-[11px] text-surface-500 leading-relaxed">{{ s.desc }}</p>
                    </div>
                  </li>
                </ol>
              </div>
            </div>

            <!-- 卡片 -->
            <div v-else-if="layout === 'cards'" class="grid gap-3 sm:grid-cols-2">
              <div v-for="(c, i) in (slide.cards || [])" :key="i"
                   :class="['rounded-xl p-4 border-l-4', cardTints[i % cardTints.length]]">
                <p class="text-[15px] font-bold text-surface-900">{{ c.title }}</p>
                <p class="mt-1.5 text-xs text-surface-600 leading-relaxed">{{ c.desc }}</p>
              </div>
            </div>

            <!-- 对比 -->
            <div v-else-if="layout === 'compare' && slide.compare" class="grid gap-3 sm:grid-cols-2">
              <div class="rounded-xl bg-surface-50 p-4">
                <p class="text-sm font-bold text-surface-900">{{ slide.compare.left?.title }}</p>
                <div class="mt-2 h-0.5 w-8 bg-surface-400"></div>
                <ul class="mt-3 space-y-2">
                  <li v-for="(it, i) in (slide.compare.left?.items || [])" :key="i"
                      class="flex items-start gap-2 text-xs text-surface-700">
                    <span class="mt-1.5 h-1.5 w-1.5 rounded-full bg-surface-400 flex-shrink-0"></span>
                    <span>{{ it }}</span>
                  </li>
                </ul>
              </div>
              <div class="rounded-xl bg-indigo-50 p-4">
                <p class="text-sm font-bold text-surface-900">{{ slide.compare.right?.title }}</p>
                <div class="mt-2 h-0.5 w-8 bg-indigo-500"></div>
                <ul class="mt-3 space-y-2">
                  <li v-for="(it, i) in (slide.compare.right?.items || [])" :key="i"
                      class="flex items-start gap-2 text-xs text-surface-700">
                    <span class="mt-1.5 h-1.5 w-1.5 rounded-full bg-indigo-500 flex-shrink-0"></span>
                    <span>{{ it }}</span>
                  </li>
                </ul>
              </div>
            </div>

            <!-- 关键数字 -->
            <div v-else-if="layout === 'metric'" class="grid gap-3 sm:grid-cols-3">
              <div v-for="(m, i) in (slide.metrics || [])" :key="i" class="rounded-xl bg-surface-50 p-4">
                <div class="h-0.5 w-8 bg-indigo-500"></div>
                <p class="mt-3 text-3xl md:text-4xl font-bold text-indigo-700 leading-none">
                  {{ m.value }}<span v-if="m.unit" class="ml-1 text-sm font-semibold text-indigo-400">{{ m.unit }}</span>
                </p>
                <p class="mt-3 text-xs text-surface-600">{{ m.label }}</p>
              </div>
            </div>

            <!-- 金句 -->
            <div v-else-if="layout === 'quote'" class="border-l-4 border-indigo-500 pl-5 py-2">
              <p class="text-lg md:text-xl font-bold text-surface-900 leading-relaxed">{{ slide.quote || slide.lead }}</p>
              <p v-if="slide.quote_by" class="mt-4 text-xs text-surface-400">— {{ slide.quote_by }}</p>
            </div>

            <!-- 表格 -->
            <div v-else-if="layout === 'table' && slide.tables?.length" class="space-y-4 overflow-x-auto">
              <table v-for="(tbl, ti) in slide.tables" :key="ti" class="w-full text-xs border-collapse">
                <tbody>
                  <tr v-for="(row, ri) in tbl" :key="ri"
                      :class="ri === 0 ? 'bg-indigo-700 text-white' : ri % 2 === 0 ? 'bg-surface-50' : ''">
                    <td v-for="(cell, ci) in row" :key="ci"
                        :class="['border border-surface-200 px-2.5 py-2', ri === 0 ? 'font-semibold' : '']">{{ cell }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 兜底：没有 bullets 的旧页面 -->
            <ul v-else class="space-y-2.5">
              <li v-for="(b, i) in slide.bullets" :key="i"
                  :class="[b.level >= 1 ? 'ml-6 text-sm text-surface-600' : 'text-[15px] text-surface-800', 'flex items-start gap-2']">
                <span :class="b.level >= 1 ? 'text-surface-300 mt-0.5' : 'text-primary-400 mt-1'">{{ b.level >= 1 ? '–' : '•' }}</span>
                <span class="flex-1">{{ b.text }}</span>
              </li>
            </ul>
          </div>

          <div class="mt-auto pt-6 flex items-center justify-between text-[10px] text-surface-300">
            <span class="truncate">{{ slide.chapter }}</span>
            <span class="font-mono">{{ String(slide.slide_index + 1).padStart(2, '0') }}</span>
          </div>
        </template>
      </div>
    </div>

    <!-- 配图：上传课件默认展开；AI 版式页折叠（避免与文本版式重复），可手动查看高清版 -->
    <div v-if="slide.has_image" class="px-4 md:px-6 pb-4">
      <button v-if="!imgVisible" type="button"
              class="w-full rounded-lg bg-surface-50 border border-surface-100 py-2 text-xs text-surface-500 hover:bg-surface-100"
              @click="loadImg">
        🖼️ {{ richLayout ? '查看整页效果图' : `此页有配图（${slide.image_kb}KB）` }} · 点击加载
      </button>
      <img v-else :src="coursewareApi.imageUrl(cwId, slide.slide_index)" :alt="slide.title"
           class="w-full rounded-lg border border-surface-100 bg-surface-50"
           @error="imgVisible = false" />
    </div>

    <div v-if="showNotes && slide.notes" class="px-6 md:px-10 pb-6 pt-4 border-t border-dashed border-surface-200">
      <p class="text-[11px] font-medium text-surface-400 mb-1.5">🗒️ 讲者备注</p>
      <p class="text-sm text-surface-600 leading-relaxed whitespace-pre-wrap">{{ slide.notes }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { coursewareApi, type SlideMeta } from '@/api/modules/courses'

const props = defineProps<{ slide: SlideMeta; cwId: number; eager?: boolean; showNotes?: boolean }>()

/** 版式：AI 生成课件带 layout；历史/上传课件按内容形态兜底 */
const layout = computed(() => {
  const raw = props.slide?.layout
  if (raw === 'cards' && !props.slide?.cards?.length) return 'bullets'
  if (raw === 'metric' && !props.slide?.metrics?.length) return 'bullets'
  if (raw === 'compare' && !props.slide?.compare) return 'bullets'
  if (raw === 'table' && !props.slide?.tables?.length) return 'bullets'
  if (raw === 'chart' && !props.slide?.chart?.values?.length) return 'bullets'
  if (raw === 'flow' && !props.slide?.steps?.length) return 'bullets'
  if (raw === 'split' && !(props.slide?.chart?.values?.length || props.slide?.steps?.length)) return 'bullets'
  return raw || (props.slide?.tables?.length ? 'table' : 'bullets')
})

/** 主点单独编号（子点不占号），与导出的 pptx 一致 */
const bulletRows = computed(() => {
  let n = 0
  return (props.slide?.bullets || []).map(b => {
    const main = (b.level || 0) < 1
    if (main) n += 1
    return { ...b, num: n }
  })
})

const chartBars = computed(() => {
  const c = props.slide?.chart
  if (!c?.values?.length) return []
  const max = Math.max(...c.values, 1)
  return c.values.map((v, i) => ({
    value: v,
    label: c.labels?.[i] ?? '',
    pct: Math.max(4, Math.round((v / max) * 100)),
    hot: v === max,
  }))
})

const lineDots = computed(() => {
  const c = props.slide?.chart
  if (!c?.values?.length) return []
  const max = Math.max(...c.values, 1)
  const step = c.values.length > 1 ? 88 / (c.values.length - 1) : 0
  return c.values.map((v, i) => ({ x: 6 + i * step, y: 42 - (v / max) * 36 }))
})
const linePoints = computed(() => lineDots.value.map(p => `${p.x},${p.y}`).join(' '))
const isDark = computed(() => layout.value === 'cover' || layout.value === 'end')
const richLayout = computed(() => !!props.slide?.layout)
const chapterNo = computed(() => String(props.slide?.chapter_no || 0).padStart(2, '0'))

const cardTints = [
  'bg-indigo-50 border-indigo-500',
  'bg-cyan-50 border-cyan-500',
  'bg-amber-50 border-amber-500',
  'bg-surface-50 border-surface-400',
]

// 版式化页面用文本渲染，配图默认折叠，避免同一页出现两份内容
const imgVisible = ref(!!props.eager && !props.slide?.layout)
function loadImg() { imgVisible.value = true }

watch(() => props.slide?.slide_index, () => {
  imgVisible.value = !!props.eager && !props.slide?.layout
})
</script>
