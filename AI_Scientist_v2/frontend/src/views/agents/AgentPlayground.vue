<template>
  <div class="space-y-6 animate-fade-in">
        <!-- 编排中枢定位说明 -->
    <div class="card border-l-4 border-l-accent-500 p-4 mb-6">
      <div class="flex items-start gap-3">
        <span class="text-2xl">🧭</span>
        <div>
          <h3 class="font-semibold text-surface-800">Agent 编排中枢</h3>
          <p class="text-sm text-surface-500 mt-1">
            在此处配置全局默认流水线模板。具体项目的执行、证据关联和反馈迭代请在
            <router-link to="/" class="text-primary-600 hover:underline font-medium">工作台</router-link>
            创建项目后进入项目详情页操作。本页面配置的模板将作为新项目的默认流水线。
          </p>
        </div>
      </div>
    </div>
    <!-- ====== 流水线构建器 ====== -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">🤖 自定义研究流水线</h2>
        <div class="flex gap-2">
          <button @click="selectAll" class="btn-secondary text-xs px-3 py-1">全选</button>
          <button @click="clearSelection" class="btn-secondary text-xs px-3 py-1">清空</button>
          <button @click="resetDefault" class="btn-secondary text-xs px-3 py-1">恢复默认</button>
        </div>
      </div>

      <!-- 已选流水线（全功能拖拽排序） -->
      <div v-if="localAgents.length > 0" class="mb-4">
        <p class="text-xs text-surface-500 mb-2">
          ↕️ 拖拽调整顺序 · ⌨️ Tab聚焦后用 ↑↓ 移动 · 点击 ✕ 移除
        </p>
        <div ref="pipelineContainer" class="flex flex-wrap gap-3 relative">
          <div
            v-for="(agent, index) in localAgents"
            :key="agent.name"
            :ref="(el) => setItemRef(el as HTMLElement, index)"
            :tabindex="0"
            role="listitem"
            :aria-label="`${agent.display_name}，位置 ${index + 1}，共 ${localAgents.length} 项`"
            draggable="true"
            @dragstart="onDragStart(index, $event)"
            @dragover.prevent="onDragOver(index)"
            @drop="onDrop(index)"
            @dragend="onDragEnd"
            @touchstart.passive="onTouchStart(index, $event)"
            @touchmove="onTouchMove($event)"
            @touchend="onTouchEnd"
            @keydown="onKeyDown(index, $event)"
            class="pipeline-chip group relative flex items-center gap-2 px-3 py-2 rounded-lg border-2 border-primary-400 bg-primary-50 select-none outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-offset-2"
            :class="{
              'dragging': dragIndex === index,
              'drag-over': dragOverIndex === index && dragIndex !== index,
              'grab-cursor': true
            }"
            :style="getFlipStyle(agent.name)"
          >
            <span class="drag-handle text-surface-400 touch-none">⠿</span>
            <span class="text-lg pointer-events-none">{{ agentIcons[agent.name] || '🤖' }}</span>
            <span class="text-sm font-medium pointer-events-none">{{ agent.display_name }}</span>
            <span class="text-[10px] text-primary-600 pointer-events-none">#{{ index + 1 }}</span>
            <button
              @click.stop="removeAgent(agent.name)"
              @keydown.enter.stop="removeAgent(agent.name)"
              type="button"
              tabindex="0"
              :aria-label="`移除 ${agent.display_name}`"
              class="ml-1 w-5 h-5 rounded-full bg-red-100 text-red-500 text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity hover:bg-red-200 focus:opacity-100 focus:ring-1 focus:ring-red-400"
            >✕</button>
          </div>
        </div>

        <!-- 触摸拖拽时的浮动幽灵元素 -->
        <Teleport to="body">
          <div
            v-if="touchDragging"
            class="fixed z-[9999] pointer-events-none px-4 py-2 rounded-lg border-2 border-primary-500 bg-primary-100 shadow-xl opacity-90 scale-105 flex items-center gap-2"
            :style="{ left: touchGhostX + 'px', top: touchGhostY + 'px', transform: 'translate(-50%, -50%)' }"
          >
            <span class="text-lg">{{ agentIcons[touchDragAgent?.name || ''] || '🤖' }}</span>
            <span class="text-sm font-medium">{{ touchDragAgent?.display_name }}</span>
          </div>
        </Teleport>
      </div>
      <div v-else class="mb-4 p-4 border-2 border-dashed border-surface-200 rounded-lg text-center text-surface-400 text-sm">
        👇 从下方点击 Agent 添加到流水线
      </div>

      <!-- 可选 Agent 池 -->
      <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <div
          v-for="agent in availableAgents"
          :key="agent.name"
          @click="addAgent(agent)"
          @keydown.enter="addAgent(agent)"
          tabindex="0"
          role="button"
          :aria-label="`添加 ${agent.display_name} 到流水线`"
          :aria-pressed="isSelected(agent.name)"
          class="p-3 rounded-xl border transition-all cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
          :class="isSelected(agent.name)
            ? 'border-primary-400 bg-primary-50 ring-1 ring-primary-300'
            : 'border-surface-200 hover:border-primary-300 hover:shadow-md'"
        >
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xl">{{ agentIcons[agent.name] || '🤖' }}</span>
            <h3 class="font-medium text-sm">{{ agent.display_name }}</h3>
            <span v-if="isSelected(agent.name)" class="ml-auto text-primary-500 text-sm">✓</span>
          </div>
          <p class="text-xs text-surface-500 line-clamp-2">{{ agent.description }}</p>
          <span v-if="agent.requires_review" class="badge-warning text-[10px] mt-1 inline-block">需审核</span>
        </div>
      </div>
    </div>

    <!-- ====== 流水线实时进度 ====== -->
    <PipelineProgress
      v-if="pipelineSteps.length > 0"
      :steps="pipelineSteps"
      :reject-reason="rejectReason"
      :iteration-count="iterationCount"
      :current-stage="currentStage"
      @retry="handleRetryReview"
      @skip="handleSkipStep"
      @abort="handleAbortPipeline"
    />

    <!-- ====== 直接对话 ====== -->
    <div class="card">
      <h2 class="text-lg font-semibold mb-4">💬 与Agent直接对话</h2>
      <div class="flex gap-3 mb-4">
        <select v-model="selectedAgent" class="input-field w-48">
          <option value="general">通用助手</option>
          <option v-for="a in agents" :key="a.name" :value="a.name">{{ a.display_name }}</option>
        </select>
        <select v-model="selectedModel" class="input-field w-48">
          <option value="qwen-turbo">Qwen-Turbo（快速）</option>
          <option value="qwen-plus">Qwen-Plus（均衡）</option>
          <option value="qwen-max">Qwen-Max（强力）</option>
        </select>
      </div>
      <div class="flex gap-3">
        <input v-model="chatInput" class="input-field flex-1" placeholder="输入你的问题..." @keyup.enter="handleChat" />
        <button @click="handleChat" :disabled="chatLoading" class="btn-primary">
          {{ chatLoading ? '思考中...' : '发送' }}
        </button>
      </div>
      <div v-if="chatReply" class="mt-4 p-4 bg-surface-50 rounded-lg">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm font-medium text-surface-600">AI回复</span>
          <span class="text-xs text-surface-400">{{ chatMeta }}</span>
        </div>
        <MarkdownView :content="chatReply" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, reactive } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { useAppStore } from '@/stores/app'
import { usePipelineStore } from '@/stores/pipeline'
import MarkdownView from '@/components/common/MarkdownView.vue'
import { useSSE } from '@/composables/useSSE'
import PipelineProgress from '@/components/pipeline/PipelineProgress.vue'

const DEFAULT_WORKFLOW = ['literature', 'design', 'analysis', 'writing', 'review']

const agentStore = useAgentStore()
const appStore = useAppStore()
const pipelineStore = usePipelineStore()

const agents = ref<any[]>([])
const localAgents = ref<Array<{ name: string; display_name: string }>>([])

// ===== Store ↔ Local 双向同步 =====
watch(
  () => pipelineStore.selectedAgents,
  (val) => {
    const localKey = localAgents.value.map(a => a.name).join('|')
    const storeKey = val.map(a => a.name).join('|')
    if (localKey !== storeKey) {
      localAgents.value = JSON.parse(JSON.stringify(val))
    }
  },
  { immediate: true, deep: true }
)

watch(
  localAgents,
  (val) => {
    const localKey = val.map(a => a.name).join('|')
    const storeKey = pipelineStore.selectedAgents.map(a => a.name).join('|')
    if (localKey !== storeKey) {
      pipelineStore.setAgents(JSON.parse(JSON.stringify(val)))
    }
  },
  { deep: true }
)

// ===== FLIP 动画系统 =====
interface FlipState {
  x: number; y: number; width: number; height: number
}

const pipelineContainer = ref<HTMLElement | null>(null)
const itemRefs = new Map<number, HTMLElement>()
const flipPrev = new Map<string, FlipState>()
const flipAnimating = reactive<Record<string, { dx: number; dy: number }>>({})

function setItemRef(el: HTMLElement | null, index: number) {
  if (el) {
    itemRefs.set(index, el)
  } else {
    itemRefs.delete(index)
  }
}

// 记录当前位置（First）
function capturePositions() {
  flipPrev.clear()
  itemRefs.forEach((el, idx) => {
    const agent = localAgents.value[idx]
    if (agent && el) {
      const rect = el.getBoundingClientRect()
      flipPrev.set(agent.name, { x: rect.left, y: rect.top, width: rect.width, height: rect.height })
    }
  })
}

// 计算反转偏移并动画（Invert + Play）
async function animateFlip() {
  await nextTick()
  const newRefs = new Map<number, HTMLElement>()
  itemRefs.forEach((el, idx) => {
    const agent = localAgents.value[idx]
    if (agent && el) {
      newRefs.set(idx, el)
    }
  })

  newRefs.forEach((el, idx) => {
    const agent = localAgents.value[idx]
    if (!agent) return
    const prev = flipPrev.get(agent.name)
    if (!prev) return
    const newRect = el.getBoundingClientRect()
    const dx = prev.x - newRect.left
    const dy = prev.y - newRect.top
    if (Math.abs(dx) < 1 && Math.abs(dy) < 1) return

    flipAnimating[agent.name] = { dx, dy }
    el.style.transform = `translate(${dx}px, ${dy}px)`
    el.style.transition = 'none'

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        el.style.transition = 'transform 0.25s cubic-bezier(0.2, 0, 0, 1)'
        el.style.transform = ''
        const onEnd = () => {
          el.style.transition = ''
          delete flipAnimating[agent.name]
          el.removeEventListener('transitionend', onEnd)
        }
        el.addEventListener('transitionend', onEnd)
      })
    })
  })
}

function getFlipStyle(_name: string) {
  return {}
}

// 监听 localAgents 变化，触发 FLIP 动画
watch(localAgents, async () => {
  await animateFlip()
}, { flush: 'post' })

// ===== SSE 初始步骤 =====
const sseInitialSteps = computed(() =>
  localAgents.value.map((a, i) => ({
    agent_name: a.name,
    display_name: a.display_name,
    status: 'pending' as const,
    step_order: i + 1
  }))
)

const { pipelineSteps, connect } = useSSE(sseInitialSteps.value)
connect()

watch(localAgents, (newVal) => {
  pipelineSteps.value = newVal.map((a, i) => ({
    agent_name: a.name,
    display_name: a.display_name,
    status: 'pending',
    step_order: i + 1
  }))
}, { deep: true })

const agentIcons: Record<string, string> = {
  literature: '📖', design: '📐', analysis: '📊', writing: '✍️', review: '🔍'
}

// ===== 桌面端拖拽（HTML5 DnD）=====
const dragIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

function onDragStart(index: number, event: DragEvent) {
  dragIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(index))
  }
  // 延迟添加 dragging 类，让浏览器先捕获拖拽图像
  requestAnimationFrame(() => {
    capturePositions()
  })
}

function onDragOver(index: number) {
  if (dragIndex.value === null || dragIndex.value === index) return
  dragOverIndex.value = index
}

function onDrop(targetIndex: number) {
  if (dragIndex.value === null || dragIndex.value === targetIndex) return
  capturePositions()
  const list = [...localAgents.value]
  const [moved] = list.splice(dragIndex.value, 1)
  list.splice(targetIndex, 0, moved)
  localAgents.value = list
  dragIndex.value = null
  dragOverIndex.value = null
}

function onDragEnd() {
  dragIndex.value = null
  dragOverIndex.value = null
}

// ===== 移动端触摸拖拽 =====
const touchDragging = ref(false)
const touchDragIndex = ref<number | null>(null)
const touchDragAgent = computed(() =>
  touchDragIndex.value !== null ? localAgents.value[touchDragIndex.value] : null
)
const touchGhostX = ref(0)
const touchGhostY = ref(0)
let touchStartX = 0
let touchStartY = 0
let touchMoved = false
const TOUCH_THRESHOLD = 10 // 像素，超过才视为拖拽（避免与滚动冲突）

function onTouchStart(index: number, event: TouchEvent) {
  const touch = event.touches[0]
  touchStartX = touch.clientX
  touchStartY = touch.clientY
  touchDragIndex.value = index
  touchMoved = false
}

function onTouchMove(event: TouchEvent) {
  if (touchDragIndex.value === null) return
  const touch = event.touches[0]
  const dx = touch.clientX - touchStartX
  const dy = touch.clientY - touchStartY

  if (!touchDragging.value && Math.sqrt(dx * dx + dy * dy) < TOUCH_THRESHOLD) return

  if (!touchDragging.value) {
    touchDragging.value = true
    capturePositions()
  }

  event.preventDefault() // 阻止页面滚动
  touchGhostX.value = touch.clientX
  touchGhostY.value = touch.clientY

  // 检测当前手指下方的元素
  const el = document.elementFromPoint(touch.clientX, touch.clientY)
  if (el) {
    const chip = el.closest('.pipeline-chip') as HTMLElement
    if (chip) {
      const parent = chip.parentElement
      if (parent) {
        const siblings = Array.from(parent.children).filter(c => c.classList.contains('pipeline-chip'))
        const targetIdx = siblings.indexOf(chip)
        if (targetIdx >= 0 && targetIdx !== touchDragIndex.value) {
          dragOverIndex.value = targetIdx
        }
      }
    }
  }
}

function onTouchEnd() {
  if (touchDragging.value && touchDragIndex.value !== null && dragOverIndex.value !== null) {
    capturePositions()
    const list = [...localAgents.value]
    const [moved] = list.splice(touchDragIndex.value, 1)
    list.splice(dragOverIndex.value, 0, moved)
    localAgents.value = list
  }
  touchDragging.value = false
  touchDragIndex.value = null
  dragOverIndex.value = null
  touchMoved = false
}

// ===== 键盘无障碍 =====
function onKeyDown(index: number, event: KeyboardEvent) {
  if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
    event.preventDefault()
    if (index <= 0) return
    capturePositions()
    const list = [...localAgents.value]
    ;[list[index - 1], list[index]] = [list[index], list[index - 1]]
    localAgents.value = list
    nextTick(() => {
      itemRefs.get(index - 1)?.focus()
    })
  } else if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
    event.preventDefault()
    if (index >= localAgents.value.length - 1) return
    capturePositions()
    const list = [...localAgents.value]
    ;[list[index], list[index + 1]] = [list[index + 1], list[index]]
    localAgents.value = list
    nextTick(() => {
      itemRefs.get(index + 1)?.focus()
    })
  } else if (event.key === 'Delete' || event.key === 'Backspace') {
    event.preventDefault()
    const agent = localAgents.value[index]
    if (agent) removeAgent(agent.name)
  }
}

// ===== 选择逻辑 =====
const isSelected = (name: string) => localAgents.value.some(a => a.name === name)
const availableAgents = computed(() => agents.value)

function addAgent(agent: any) {
  if (!isSelected(agent.name)) {
    localAgents.value = [...localAgents.value, { name: agent.name, display_name: agent.display_name }]
  }
}

function removeAgent(name: string) {
  localAgents.value = localAgents.value.filter(a => a.name !== name)
}

function selectAll() {
  capturePositions()
  localAgents.value = agents.value.map(a => ({ name: a.name, display_name: a.display_name }))
}

function clearSelection() {
  capturePositions()
  localAgents.value = []
}

function resetDefault() {
  capturePositions()
  localAgents.value = DEFAULT_WORKFLOW
    .map(name => {
      const a = agents.value.find(ag => ag.name === name)
      return a ? { name: a.name, display_name: a.display_name } : null
    })
    .filter(Boolean) as Array<{ name: string; display_name: string }>
}

// ===== 审核拒绝 / 失败处理 =====
const rejectReason = ref('')

const iterationCount = computed(() => {
  const versions = pipelineSteps.value.map(s => s.version).filter(v => v != null)
  return versions.length > 0 ? Math.max(...versions) : 1
})

const currentStage = computed(() => {
  const active = pipelineSteps.value.find(s => s.status === 'running' || s.status === 'pending')
  if (active) return active.display_name || active.agent_name
  const last = pipelineSteps.value[pipelineSteps.value.length - 1]
  return last?.display_name || last?.agent_name || ''
})

watch(pipelineSteps, (steps) => {
  const rejected = steps.find(s => s.status === 'rejected' || s.status === 'failed')
  if (rejected) {
    rejectReason.value = (rejected as any).reason || `${rejected.display_name || rejected.agent_name} 未通过，请修改后重试`
  } else {
    rejectReason.value = ''
  }
}, { deep: true })

async function handleRetryReview() {
  appStore.showToast('正在重新提交...', 'info')
  try {
    await pipelineStore.retryCurrentStep()
    connect()
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '重试失败', 'error')
  }
}

async function handleSkipStep() {
  try {
    await pipelineStore.skipCurrentStep()
    connect()
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '跳过失败', 'error')
  }
}

async function handleAbortPipeline() {
  if (!confirm('确定要终止当前流水线吗？')) return
  try {
    await pipelineStore.abortPipeline()
    appStore.showToast('流水线已终止', 'success')
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '终止失败', 'error')
  }
}
// ===== 对话逻辑 =====
const selectedAgent = ref('general')
const selectedModel = ref('qwen-plus')
const chatInput = ref('')
const chatReply = ref('')
const chatMeta = ref('')
const chatLoading = ref(false)

onMounted(async () => {
  await agentStore.fetchAgents()
  agents.value = agentStore.agents
  if (pipelineStore.selectedAgents.length === 0) {
    resetDefault()
  }
})

async function handleChat() {
  if (!chatInput.value.trim()) return
  chatLoading.value = true
  chatReply.value = ''
  try {
    const res = await agentStore.directChat(chatInput.value, selectedAgent.value, selectedModel.value)
    chatReply.value = res.data.reply
    chatMeta.value = `${res.data.model} · ${res.data.tokens.input + res.data.tokens.output} tokens · ¥${res.data.cost.toFixed(4)}`
    chatInput.value = ''
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '对话失败', 'error')
  } finally { chatLoading.value = false }
}
</script>

<style scoped>
.pipeline-chip {
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
  cursor: grab;
  touch-action: pan-y;
}
.pipeline-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.pipeline-chip:active {
  cursor: grabbing;
}
.pipeline-chip.dragging {
  opacity: 0.4;
  transform: scale(0.95);
  box-shadow: none;
}
.pipeline-chip.drag-over {
  box-shadow: 0 0 0 3px rgb(var(--color-primary-500, 59 130 246)), 0 4px 12px rgba(0,0,0,0.1);
  transform: scale(1.02);
}
.grab-cursor {
  cursor: grab;
}
.grab-cursor:active {
  cursor: grabbing;
}
</style>
