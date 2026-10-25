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

    <div class="p-6 md:p-8">
      <div class="flex items-baseline gap-2 mb-1">
        <span class="text-[11px] text-surface-300 font-mono">{{ String(slide.slide_index + 1).padStart(2, '0') }}</span>
        <h2 class="text-xl md:text-2xl font-bold text-surface-800">{{ slide.title || '（无标题页）' }}</h2>
      </div>

      <ul class="mt-4 space-y-2.5">
        <li v-for="(b, i) in slide.bullets" :key="i"
            :class="[b.level >= 1 ? 'ml-6 text-sm text-surface-600' : 'text-base md:text-[17px] text-surface-800', 'flex items-start gap-2']">
          <span :class="b.level >= 1 ? 'text-surface-300 mt-0.5' : 'text-primary-400 mt-1'">{{ b.level >= 1 ? '–' : '•' }}</span>
          <span class="flex-1">{{ b.text }}</span>
        </li>
      </ul>

      <div v-if="slide.tables?.length" class="mt-5 space-y-4 overflow-x-auto">
        <table v-for="(tbl, ti) in slide.tables" :key="ti" class="w-full text-xs border-collapse">
          <tbody>
            <tr v-for="(row, ri) in tbl" :key="ri" :class="ri === 0 ? 'bg-surface-50 font-medium' : ''">
              <td v-for="(cell, ci) in row" :key="ci" class="border border-surface-200 px-2.5 py-1.5">{{ cell }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 配图：仅在需要时加载（这就是首屏快的原因） -->
      <div v-if="slide.has_image" class="mt-6">
        <div v-if="!imgVisible" class="w-full aspect-video rounded-lg bg-surface-100 flex items-center justify-center text-xs text-surface-400 cursor-pointer hover:bg-surface-200"
             @click="loadImg">
          🖼️ 此页有配图（{{ slide.image_kb }}KB）· 点击加载
        </div>
        <img v-else :src="coursewareApi.imageUrl(cwId, slide.slide_index)" :alt="slide.title"
             class="w-full rounded-lg border border-surface-100 bg-surface-50"
             @error="imgVisible = false" />
      </div>

      <div v-if="showNotes && slide.notes" class="mt-5 pt-4 border-t border-dashed border-surface-200">
        <p class="text-[11px] font-medium text-surface-400 mb-1.5">🗒️ 讲者备注</p>
        <p class="text-sm text-surface-600 leading-relaxed whitespace-pre-wrap">{{ slide.notes }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { coursewareApi, type SlideMeta } from '@/api/modules/courses'

const props = defineProps<{ slide: SlideMeta; cwId: number; eager?: boolean; showNotes?: boolean }>()

const imgVisible = ref(!!props.eager)
function loadImg() { imgVisible.value = true }

watch(() => props.slide?.slide_index, () => { imgVisible.value = !!props.eager })
</script>
