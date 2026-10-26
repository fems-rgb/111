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
            <!-- 要点 -->
            <ul v-if="layout === 'bullets'" class="space-y-4">
              <li v-for="(b, i) in slide.bullets" :key="i"
                  :class="[b.level >= 1 ? 'ml-10' : '', 'flex items-start gap-3']">
                <span v-if="b.level >= 1" class="mt-2.5 h-0.5 w-3 bg-indigo-300 flex-shrink-0"></span>
                <span v-else
                      class="mt-0.5 h-7 w-7 flex-shrink-0 rounded-lg bg-indigo-50 text-indigo-600 text-xs font-bold flex items-center justify-center">
                  {{ i + 1 }}
                </span>
                <span :class="[b.level >= 1 ? 'text-sm text-surface-600' : 'text-[15px] md:text-base text-surface-800 font-medium', 'leading-relaxed pt-1']">
                  {{ b.text }}
                </span>
              </li>
            </ul>

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
  return raw || (props.slide?.tables?.length ? 'table' : 'bullets')
})
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
