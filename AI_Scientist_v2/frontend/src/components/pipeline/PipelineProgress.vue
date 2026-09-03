<template>
  <div class="card" v-if="steps.length > 0">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-lg font-semibold">⚙️ 研究流水线进度</h2>
      <div class="flex items-center gap-3 text-sm">
        <span class="text-surface-500">{{ completedCount }}/{{ steps.length }} 步</span>
        <span v-if="etaText" class="text-primary-600 font-medium">⏱ {{ etaText }}</span>
        <span v-if="isRejected" class="text-red-500 font-medium">❌ 审核未通过</span>
        <button @click="$emit('restart-project')" class="text-xs px-2 py-1 rounded border border-orange-200 text-orange-600 hover:bg-orange-50 transition-colors" title="重启整个项目">🔄 重启</button>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="w-full h-3 bg-surface-100 rounded-full overflow-hidden mb-4">
      <div
        class="h-full rounded-full transition-all duration-500 ease-out"
        :class="isRejected ? 'bg-red-500' : isCompleted ? 'bg-green-500' : 'bg-primary-500'"
        :style="{ width: progressPercent + '%' }"
      />
    </div>

    <!-- 步骤节点 -->
    <div class="flex items-center gap-2 overflow-x-auto pb-2">
      <template v-for="(step, idx) in steps" :key="step.agent_name">
        <div class="flex flex-col items-center min-w-[100px]">
          <div class="w-10 h-10 rounded-full flex items-center justify-center text-lg border-2 transition-all"
               :class="{
                 'border-primary-500 bg-primary-50 animate-pulse': step.status === 'running',
                 'border-green-500 bg-green-50': step.status === 'completed',
                 'border-red-500 bg-red-50': step.status === 'failed' || step.status === 'rejected',
                 'border-surface-300 bg-surface-50': step.status === 'pending'
               }">
            {{ step.status === 'completed' ? '✅' : (step.status === 'failed' || step.status === 'rejected') ? '❌' : step.status === 'running' ? '🔄' : '⏳' }}
          </div>
          <span class="text-xs mt-1 font-medium text-center">{{ stepName(step.display_name || step.agent_name) }}</span>
          <span class="text-[10px]" :class="(step.status === 'rejected' || step.status === 'failed') ? 'text-red-500' : 'text-surface-400'">
            {{ statusLabel(step.status) }}
          </span>
          <span v-if="step.elapsed != null" class="text-[10px]" :class="(step.elapsed||0) > 1800 ? 'text-red-500 font-medium' : 'text-surface-400'">{{ humanize(step.elapsed||0) }}<template v-if="(step.elapsed||0) > 1800"> ⚠️可能卡死</template></span>
          <button v-if="step.status === 'running' && (step.elapsed||0) > 1800" @click="$emit('restart-step', step.agent_name)" class="mt-1 text-[10px] px-2 py-0.5 bg-orange-100 text-orange-700 rounded hover:bg-orange-200 transition-colors whitespace-nowrap">🔄 重启此步</button>
        </div>
        <div v-if="idx < steps.length - 1" class="flex-1 h-0.5 min-w-[30px]"
             :class="steps[idx].status === 'completed' && steps[idx+1].status !== 'pending' ? 'bg-primary-400' : 'bg-surface-200'" />
      </template>
    </div>

    <!-- 赛道一增量：科研闭环流程图 -->
    <div class="closure-loop mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
      <div class="text-xs font-semibold text-blue-800 mb-2">🔬 科研闭环状态</div>
      <div class="flex items-center gap-1 flex-wrap text-[11px]">
        <span class="loop-node" :class="loopClass('understand')">①问题理解</span>
        <span class="loop-arrow">→</span>
        <span class="loop-node" :class="loopClass('knowledge_gap')">②知识缺口</span>
        <span class="loop-arrow">→</span>
        <span class="loop-node" :class="loopClass('literature')">③证据获取</span>
        <span class="loop-arrow">→</span>
        <span class="loop-node" :class="loopClass('hypothesis')">④假设生成</span>
        <span class="loop-arrow">→</span>
        <span class="loop-node" :class="loopClass('validator')">⑤核验筛选</span>
        <span class="loop-arrow">→</span>
        <span class="loop-node" :class="loopClass('experiment_plan')">⑥研究计划</span>
        <span class="loop-arrow">→</span>
        <span class="loop-node" :class="loopClass('reflection')">⑦反馈迭代</span>
        <span class="loop-arrow loop-back">↩</span>
      </div>
      <div v-if="iterationCount > 0" class="mt-2 text-[11px] text-blue-700">
        🔄 已迭代 {{ iterationCount }} 轮 | 当前阶段: {{ currentStage }}
      </div>
    </div>

    <!-- 审核拒绝 / 失败时的操作面板 -->
    <div v-if="isRejected" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
      <div class="flex items-start gap-3">
        <span class="text-2xl">🚫</span>
        <div class="flex-1">
          <h3 class="font-medium text-red-800 mb-1">流水线已停止</h3>
          <p class="text-sm text-red-600 mb-3">{{ rejectReason || '请检查内容后重新提交' }}</p>
          <div class="flex flex-wrap gap-2">
            <button @click="$emit('retry')" class="btn-primary text-sm px-4 py-2">🔄 修改后重新提交</button>
            <button @click="$emit('skip')" class="btn-secondary text-sm px-4 py-2">⏭ 跳过此步骤</button>
            <button @click="$emit('abort')" class="btn-secondary text-sm px-4 py-2 text-red-600 hover:text-red-700">✕ 终止流水线</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 全部完成提示 -->
    <div v-if="isCompleted" class="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg text-center">
      <span class="text-2xl">🎉</span>
      <p class="text-green-800 font-medium mt-1">流水线已全部完成！</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface PipelineStep {
  agent_name: string
  display_name?: string
  status: string
  step_order?: number
  version?: number
  elapsed?: number
  reason?: string
}

const props = defineProps<{
  steps: PipelineStep[]
  rejectReason?: string
  iterationCount?: number
  currentStage?: string
}>()

defineEmits<{ retry: []; skip: []; abort: []; 'restart-step': [agentName: string]; 'restart-project': [] }>()

const completedCount = computed(() => props.steps.filter(s => s.status === 'completed').length)
const isCompleted = computed(() => props.steps.length > 0 && props.steps.every(s => s.status === 'completed'))
const isRejected = computed(() => props.steps.some(s => s.status === 'rejected' || s.status === 'failed'))

const progressPercent = computed(() => {
  if (props.steps.length === 0) return 0
  return Math.round((completedCount.value / props.steps.length) * 100)
})

// ETA：基于已完成步骤平均耗时 × 剩余步骤数
const etaText = computed(() => {
  const completed = props.steps.filter(s => s.status === 'completed' && s.elapsed)
  if (completed.length === 0 || isCompleted.value || isRejected.value) return ''
  const avgTime = completed.reduce((sum, s) => sum + (s.elapsed || 0), 0) / completed.length
  const remaining = props.steps.filter(s => s.status === 'pending' || s.status === 'running').length
  if (remaining === 0) return ''
  const etaSeconds = Math.round(avgTime * remaining)
  if (etaSeconds < 60) return `约 ${etaSeconds}秒`
  return `约 ${Math.floor(etaSeconds / 60)}分${etaSeconds % 60}秒`
})

const stageAgentMap: Record<string, string[]> = {
  understand: ['task_router'],
  knowledge_gap: ['knowledge_gap'],
  literature: ['literature'],
  hypothesis: ['hypothesis', 'design'],
  validator: ['hypothesis_validator'],
  experiment_plan: ['experiment_plan'],
  reflection: ['reflection']
}
function loopClass(stage: string): string {
  const agents = stageAgentMap[stage] || []
  const matched = props.steps.filter(s => agents.includes(s.agent_name))
  if (matched.some(s => s.status === 'running')) return 'loop-running'
  if (matched.every(s => s.status === 'completed') && matched.length > 0) return 'loop-done'
  if (matched.some(s => s.status === 'failed')) return 'loop-failed'
  return 'loop-pending'
}
const iterationCount = computed(() => props.iterationCount ?? 0)
const currentStage = computed(() => props.currentStage ?? '未开始')


function humanize(s: number): string {
  if (s < 60) return `${s}秒`
  if (s < 3600) return `${Math.floor(s/60)}分${s%60}秒`
  return `${Math.floor(s/3600)}时${Math.floor((s%3600)/60)}分`
}

function stepName(key: string): string {
  const map: Record<string, string> = {
    knowledge_gap: '知识缺口识别',
    literature: '文献综述',
    literature_review: '文献综述',
    hypothesis: '假设生成',
    design: '研究设计',
    experiment_plan: '实验计划',
    experiment: '实验计划',
    analysis: '数据分析',
    data_analysis: '数据分析',
    writing: '学术写作',
    review: '同行评审',
    peer_review: '同行评审',
    reflection: '反思迭代',
    validator: '假设校验',
    hypothesis_validator: '假设校验',
    task_router: '任务路由'
  }
  return map[key] || key
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '等待中', running: '执行中', completed: '已完成',
    failed: '失败', rejected: '未通过', skipped: '已跳过'
  }
  return map[status] || status
}
</script>
<style scoped>
.loop-node{padding:2px 8px;border-radius:10px;border:1px solid #bfdbfe;background:#fff;color:#1e40af;white-space:nowrap}
.loop-arrow{color:#93c5fd;font-weight:700}
.loop-back{color:#f59e0b;font-size:13px}
.loop-running{background:#dbeafe;border-color:#3b82f6;animation:pulse 1.5s infinite}
.loop-done{background:#d1fae5;border-color:#10b981;color:#065f46}
.loop-failed{background:#fee2e2;border-color:#ef4444;color:#991b1b}
.loop-pending{opacity:.5}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}
</style>
