<template>
  <div class="hypo-panel">
    <div class="hypo-header">
      <span class="hypo-title">💡 假设证据链</span>
      <button class="hypo-refresh" @click="load">🔄</button>
    </div>
    <div v-if="loading" class="hypo-loading">加载中...</div>
    <div v-else-if="!hypotheses.length" class="hypo-empty">暂无假设，运行 hypothesis Agent 后自动生成</div>
    <div v-for="h in hypotheses" :key="h.id" class="hypo-card">
      <div class="hypo-id">{{ h.hypo_id }} <span class="hypo-ver">v{{ h.version }}</span></div>
      <div class="hypo-statement">{{ h.statement }}</div>
      <div class="hypo-meta">
        <span class="hypo-score" :class="scoreClass(h.testability_score)">可验证性 {{ h.testability_score }}/10</span>
        <span class="hypo-status">{{ h.status }}</span>
      </div>
      <details v-if="h.evidence_chain" class="hypo-evidence">
        <summary>证据链</summary>
        <pre>{{ h.evidence_chain }}</pre>
      </details>
      <!-- 赛道一增量：5维评分展示 -->
      <div v-if="h.falsifiability_score" class="hypo-scores-row">
        <span class="mini-score">可证伪 {{ h.falsifiability_score }}/10</span>
        <span class="mini-score">证据一致 {{ h.evidence_consistency ?? '-' }}/10</span>
        <span class="mini-score">新颖性 {{ h.novelty_score ?? '-' }}/10</span>
      </div>
      <!-- 赛道一增量：反对证据 -->
      <details v-if="h.counter_evidence && h.counter_evidence !== '暂无'" class="hypo-counter">
        <summary>⚠️ 反对证据</summary>
        <pre>{{ h.counter_evidence }}</pre>
      </details>
      <!-- 赛道一增量：人工反馈按钮 -->
      <div class="hypo-feedback-btns">
        <button class="fb-btn fb-accept" @click="$emit('feedback', h.hypo_id, 'accept')">✅ 采纳</button>
        <button class="fb-btn fb-reject" @click="$emit('feedback', h.hypo_id, 'reject')">❌ 拒绝</button>
        <button class="fb-btn fb-revise" @click="$emit('feedback', h.hypo_id, 'revise')">✏️ 修改</button>
      </div>
    </div>
    <div v-if="iterations.length" class="iter-section">
      <div class="iter-title">🔄 迭代历史</div>
      <div v-for="it in iterations" :key="it.iteration_num" class="iter-row">
        <span class="iter-num">#{{ it.iteration_num }}</span>
        <span class="iter-score">{{ it.score_before }} → {{ it.score_after }}</span>
        <span class="iter-time">{{ it.created_at?.slice(0, 16) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { getHypotheses, getIterations, type Hypothesis, type IterationRecord } from '@/api/modules/hypothesis'

const props = defineProps<{ projectId: number }>()
const hypotheses = ref<Hypothesis[]>([])
const iterations = ref<IterationRecord[]>([])
const loading = ref(false)

async function load() {
  if (!props.projectId) return
  loading.value = true
  try {
    const [hRes, iRes] = await Promise.all([getHypotheses(props.projectId), getIterations(props.projectId)])
    hypotheses.value = (hRes as any)?.hypotheses ?? hRes ?? []
    iterations.value = (iRes as any)?.iterations ?? iRes ?? []
  } catch (e) { console.error('load hypotheses failed', e) }
  finally { loading.value = false }
}

function scoreClass(s: number) {
  if (s >= 7) return 'score-high'
  if (s >= 4) return 'score-mid'
  return 'score-low'
}

onMounted(load)
watch(() => props.projectId, load)
defineExpose({ refresh: load })
</script>

<style scoped>
.hypo-panel{padding:12px;font-size:13px;border-left:1px solid #e5e7eb;height:100%;overflow-y:auto;background:#fafbfc;min-width:280px;max-width:360px}
.hypo-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.hypo-title{font-weight:700;font-size:14px}
.hypo-refresh{background:none;border:none;cursor:pointer;font-size:16px}
.hypo-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:10px;margin-bottom:8px}
.hypo-id{font-weight:700;color:#1a73e8;margin-bottom:4px}
.hypo-ver{font-weight:400;font-size:11px;color:#999;margin-left:4px}
.hypo-statement{line-height:1.5;margin-bottom:6px}
.hypo-meta{display:flex;gap:8px;font-size:12px}
.hypo-score{padding:1px 6px;border-radius:4px}
.score-high{background:#d4edda;color:#155724}
.score-mid{background:#fff3cd;color:#856404}
.score-low{background:#f8d7da;color:#721c24}
.hypo-status{color:#666}
.hypo-evidence summary{cursor:pointer;font-size:12px;color:#1a73e8;margin-top:4px}
.hypo-evidence pre{white-space:pre-wrap;font-size:11px;background:#f5f5f5;padding:6px;border-radius:4px;margin-top:4px}
.iter-section{margin-top:16px;border-top:1px solid #e5e7eb;padding-top:10px}
.iter-title{font-weight:700;margin-bottom:6px}
.iter-row{display:flex;gap:8px;font-size:12px;padding:3px 0;align-items:center}
.iter-num{font-weight:700;color:#1a73e8;min-width:28px}
.iter-score{color:#333}
.iter-time{color:#999;margin-left:auto}
.hypo-loading,.hypo-empty{text-align:center;color:#999;padding:24px 0}
.hypo-scores-row{display:flex;gap:6px;margin-top:6px;flex-wrap:wrap}
.mini-score{font-size:11px;padding:1px 5px;border-radius:3px;background:#e8f0fe;color:#1a73e8}
.hypo-counter summary{cursor:pointer;font-size:12px;color:#d93025;margin-top:4px}
.hypo-counter pre{white-space:pre-wrap;font-size:11px;background:#fce8e6;padding:6px;border-radius:4px;margin-top:4px}
.hypo-feedback-btns{display:flex;gap:6px;margin-top:8px}
.fb-btn{padding:4px 10px;border:1px solid #ddd;border-radius:4px;font-size:11px;cursor:pointer;background:#fff}
.fb-accept:hover{background:#d4edda;border-color:#28a745}
.fb-reject:hover{background:#f8d7da;border-color:#dc3545}
.fb-revise:hover{background:#fff3cd;border-color:#ffc107}
</style>

