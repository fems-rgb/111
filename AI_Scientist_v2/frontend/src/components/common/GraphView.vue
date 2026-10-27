<template>
  <div class="graph-view" ref="rootRef">
    <!-- 顶部工具条 -->
    <div class="gv-toolbar">
      <span class="gv-meta" v-if="payload?.nodes?.length">
        节点 {{ payload.nodes.length }} · 关系 {{ payload.edges.length }}
        <em v-if="payload.model_used">· {{ payload.model_used }}</em>
      </span>
      <div class="gv-actions">
        <button class="gv-btn" :disabled="loading" @click="fit">{{ '居中' }}</button>
        <button class="gv-btn" :disabled="loading" @click="rebuild">{{ loading ? '生成中…' : 'AI 重新生成' }}</button>
      </div>
    </div>

    <!-- 加载骨架 -->
    <div v-if="loading && !payload?.nodes?.length" class="gv-skeleton">
      <div class="gv-sk-dot" v-for="i in 8" :key="i" :style="skelStyle(i)"></div>
      <p>图谱生成中…</p>
    </div>

    <!-- 空态 -->
    <div v-else-if="!payload?.nodes?.length" class="gv-empty">
      <p class="gv-empty-ico">🕸️</p>
      <p class="gv-empty-tip">{{ emptyTip }}</p>
      <button class="gv-btn gv-btn-primary" @click="rebuild">AI 生成图谱</button>
    </div>

    <!-- 主画布：SVG 力导向 -->
    <svg v-else ref="svgRef" class="gv-svg"
         @wheel.prevent="onWheel"
         @pointerdown="onBgDown"
         @pointermove="onMove"
         @pointerup="onUp"
         @pointerleave="onUp">
      <g :transform="viewTransform">
        <line v-for="(e, i) in layoutEdges" :key="'e'+i"
              :x1="e.x1" :y1="e.y1" :x2="e.x2" :y2="e.y2"
              class="gv-edge" />
        <text v-for="(e, i) in layoutEdges" :key="'el'+i"
              :x="(e.x1 + e.x2) / 2" :y="(e.y1 + e.y2) / 2 - 2"
              class="gv-edge-label">{{ e.rel }}</text>
        <g v-for="n in layoutNodes" :key="n.id"
           class="gv-node" :class="'g-' + n.group"
           :transform="`translate(${n.x},${n.y})`"
           @pointerdown.stop="onNodeDown(n, $event)"
           @click.stop="onNodeClick(n)">
          <circle :r="nodeRadius(n)" />
          <text y="4" class="gv-label">{{ n.label }}</text>
        </g>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { graphsApi, type GraphScope, type GraphPayload, type GraphNode } from '@/api/modules/graphs'

interface LayoutNode extends GraphNode { x: number; y: number; vx: number; vy: number; deg: number }
interface LayoutEdge { x1: number; y1: number; x2: number; y2: number; rel: string }

const props = defineProps<{
  scope: GraphScope
  scopeId: string | number
  emptyTip?: string
  autoLoad?: boolean
}>()
const emit = defineEmits<{ (e: 'node-click', node: GraphNode): void }>()

const W = 800, H = 480
const rootRef = ref<HTMLElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)
const payload = ref<GraphPayload | null>(null)
const loading = ref(false)
const nodes = ref<LayoutNode[]>([])
const edges = ref<{ s: string; t: string; rel: string }[]>([])

// 视口变换（缩放 + 平移）
const scale = ref(1)
const tx = ref(0)
const ty = ref(0)
const viewTransform = computed(() => `translate(${tx.value},${ty.value}) scale(${scale.value})`)

const emptyTip = computed(() => props.emptyTip || '还没有知识图谱，让 AI 从材料里抽取一份')

// ── 数据 ──
async function load() {
  loading.value = true
  try {
    const r = await graphsApi.get(props.scope, props.scopeId)
    payload.value = r.data
    applyData(r.data)
  } catch { /* 空/失败按空态处理 */ }
  finally { loading.value = false }
}

async function rebuild() {
  loading.value = true
  try {
    const r = await graphsApi.rebuild(props.scope, props.scopeId, {})
    payload.value = r.data
    applyData(r.data)
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '生成失败，请稍后重试'
    // 通过内联 toast 复用 app store（若已引入）；此处降级为 alert，避免强耦合
    if (typeof window !== 'undefined') window.alert(String(msg))
  } finally { loading.value = false }
}

function applyData(p: GraphPayload | null) {
  if (!p?.nodes?.length) { nodes.value = []; edges.value = []; return }
  const deg: Record<string, number> = {}
  for (const e of p.edges || []) {
    deg[e[0]] = (deg[e[0]] || 0) + 1
    deg[e[1]] = (deg[e[1]] || 0) + 1
  }
  // 初始按圆形散布，减少初帧重叠
  const n = p.nodes.length
  nodes.value = p.nodes.map((nd, i) => ({
    ...nd,
    x: W / 2 + Math.cos((i / n) * Math.PI * 2) * 180 + (Math.random() - 0.5) * 20,
    y: H / 2 + Math.sin((i / n) * Math.PI * 2) * 140 + (Math.random() - 0.5) * 20,
    vx: 0, vy: 0, deg: deg[nd.id] || 0,
  }))
  const idx: Record<string, LayoutNode> = {}
  for (const nd of nodes.value) idx[nd.id] = nd
  edges.value = (p.edges || []).map(e => ({ s: e[0], t: e[1], rel: e[2] || 'related' })).filter(e => idx[e.s] && idx[e.t])
  simulate()
  fit()
}

// ── 力导向（简单版：斥力 + 弹簧 + 中心引力） ──
function simulate(iterations = 220) {
  const k = 90              // 理想边长
  const repulse = 6500
  const center = { x: W / 2, y: H / 2 }
  for (let it = 0; it < iterations; it++) {
    const alpha = 1 - it / iterations
    for (let i = 0; i < nodes.value.length; i++) {
      const a = nodes.value[i]
      for (let j = i + 1; j < nodes.value.length; j++) {
        const b = nodes.value[j]
        let dx = a.x - b.x, dy = a.y - b.y
        let d2 = dx * dx + dy * dy
        if (d2 < 1) { dx = Math.random() - 0.5; dy = Math.random() - 0.5; d2 = 1 }
        const d = Math.sqrt(d2)
        const f = (repulse / d2) * alpha
        a.vx += (dx / d) * f; a.vy += (dy / d) * f
        b.vx -= (dx / d) * f; b.vy -= (dy / d) * f
      }
    }
    const map: Record<string, LayoutNode> = {}
    for (const n of nodes.value) map[n.id] = n
    for (const e of edges.value) {
      const s = map[e.s], t = map[e.t]
      const dx = t.x - s.x, dy = t.y - s.y
      const d = Math.sqrt(dx * dx + dy * dy) || 1
      const f = ((d - k) / d) * 0.35 * alpha
      s.vx += dx * f; s.vy += dy * f
      t.vx -= dx * f; t.vy -= dy * f
    }
    for (const n of nodes.value) {
      n.vx += (center.x - n.x) * 0.015 * alpha
      n.vy += (center.y - n.y) * 0.015 * alpha
      n.vx *= 0.85; n.vy *= 0.85
      n.x += Math.max(-18, Math.min(18, n.vx))
      n.y += Math.max(-18, Math.min(18, n.vy))
    }
  }
}

const layoutNodes = computed(() => nodes.value)
const layoutEdges = computed<LayoutEdge[]>(() => {
  const map: Record<string, LayoutNode> = {}
  for (const n of nodes.value) map[n.id] = n
  return edges.value.map(e => {
    const s = map[e.s], t = map[e.t]
    return { x1: s.x, y1: s.y, x2: t.x, y2: t.y, rel: e.rel }
  })
})

function nodeRadius(n: LayoutNode) {
  return 16 + Math.min(14, n.deg * 2)
}

function skelStyle(i: number) {
  const angle = (i / 8) * Math.PI * 2
  return {
    left: `${50 + Math.cos(angle) * 30}%`,
    top: `${50 + Math.sin(angle) * 30}%`,
    animationDelay: `${i * 0.1}s`,
  }
}

// ── 视口交互 ──
function fit() {
  if (!nodes.value.length) return
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const n of nodes.value) {
    minX = Math.min(minX, n.x); maxX = Math.max(maxX, n.x)
    minY = Math.min(minY, n.y); maxY = Math.max(maxY, n.y)
  }
  const pad = 60
  const w = maxX - minX + pad * 2, h = maxY - minY + pad * 2
  scale.value = Math.min(1.6, Math.max(0.4, Math.min(W / w, H / h)))
  tx.value = W / 2 - ((minX + maxX) / 2) * scale.value
  ty.value = H / 2 - ((minY + maxY) / 2) * scale.value
}

function onWheel(ev: WheelEvent) {
  const rect = svgRef.value?.getBoundingClientRect()
  if (!rect) return
  const mx = ev.clientX - rect.left, my = ev.clientY - rect.top
  const factor = ev.deltaY < 0 ? 1.12 : 0.9
  const ns = Math.max(0.35, Math.min(3, scale.value * factor))
  // 以指针为中心缩放
  tx.value = mx - (mx - tx.value) * (ns / scale.value)
  ty.value = my - (my - ty.value) * (ns / scale.value)
  scale.value = ns
}

interface DragState { kind: 'pan' | 'node'; start: { x: number; y: number }; origTx?: number; origTy?: number; node?: LayoutNode; origX?: number; origY?: number; moved: boolean }
const drag = ref<DragState | null>(null)

function toWorld(x: number, y: number) {
  return { x: (x - tx.value) / scale.value, y: (y - ty.value) / scale.value }
}

function onBgDown(ev: PointerEvent) {
  const rect = svgRef.value!.getBoundingClientRect()
  drag.value = { kind: 'pan', start: { x: ev.clientX - rect.left, y: ev.clientY - rect.top },
                 origTx: tx.value, origTy: ty.value, moved: false }
  ;(ev.target as Element).setPointerCapture?.(ev.pointerId)
}

function onNodeDown(n: LayoutNode, ev: PointerEvent) {
  const rect = svgRef.value!.getBoundingClientRect()
  drag.value = { kind: 'node', node: n,
                 start: { x: ev.clientX - rect.left, y: ev.clientY - rect.top },
                 origX: n.x, origY: n.y, moved: false }
  ;(ev.target as Element).setPointerCapture?.(ev.pointerId)
}

function onMove(ev: PointerEvent) {
  if (!drag.value) return
  const rect = svgRef.value!.getBoundingClientRect()
  const mx = ev.clientX - rect.left, my = ev.clientY - rect.top
  const dx = mx - drag.value.start.x, dy = my - drag.value.start.y
  if (Math.abs(dx) + Math.abs(dy) > 2) drag.value.moved = true
  if (drag.value.kind === 'pan') {
    tx.value = (drag.value.origTx || 0) + dx
    ty.value = (drag.value.origTy || 0) + dy
  } else if (drag.value.node) {
    const w = toWorld(mx, my)
    drag.value.node.x = w.x
    drag.value.node.y = w.y
  }
}

function onUp() {
  // 节点被拖后轻微再收敛一次
  if (drag.value?.kind === 'node' && drag.value.moved) simulate(40)
  drag.value = null
}

function onNodeClick(n: LayoutNode) {
  if (drag.value?.moved) return
  emit('node-click', { id: n.id, label: n.label, group: n.group })
}

watch(() => [props.scope, props.scopeId], () => { if (props.autoLoad !== false) load() })
onMounted(() => { if (props.autoLoad !== false) load() })
onUnmounted(() => { drag.value = null })

defineExpose({ reload: load })
</script>

<style scoped>
.graph-view { width: 100%; height: 100%; min-height: 340px; display: flex; flex-direction: column;
              background: var(--surface-0, #fff); border: 1px solid var(--surface-200, #e5e7eb); border-radius: 12px; overflow: hidden }
.gv-toolbar { display: flex; justify-content: space-between; align-items: center;
              padding: 8px 12px; border-bottom: 1px solid var(--surface-200, #e5e7eb); background: var(--surface-50, #fafafa) }
.gv-meta { font-size: 12px; color: var(--surface-500, #6b7280) }
.gv-meta em { font-style: normal; margin-left: 6px; padding: 1px 6px; border-radius: 999px;
              background: var(--surface-200, #e5e7eb); color: var(--surface-700, #374151) }
.gv-actions { display: flex; gap: 6px }
.gv-btn { font-size: 12px; padding: 4px 10px; border-radius: 6px; border: 1px solid var(--surface-300, #d1d5db);
          background: #fff; color: var(--surface-700, #374151); cursor: pointer; transition: all .15s }
.gv-btn:hover:not(:disabled) { background: var(--surface-100, #f3f4f6) }
.gv-btn:disabled { opacity: .5; cursor: not-allowed }
.gv-btn-primary { background: var(--primary-500, #4f46e5); color: #fff; border-color: transparent }
.gv-btn-primary:hover { background: var(--primary-600, #4338ca) }
.gv-svg { flex: 1; width: 100%; height: auto; touch-action: none; cursor: grab }
.gv-svg:active { cursor: grabbing }
.gv-edge { stroke: #94a3b8; stroke-width: 1.2; stroke-opacity: .55 }
.gv-edge-label { font-size: 9px; fill: #64748b; text-anchor: middle; pointer-events: none; opacity: .8 }
.gv-node { cursor: pointer }
.gv-node circle { fill: #6366f1; stroke: #fff; stroke-width: 2; transition: fill .15s }
.gv-node:hover circle { fill: #4338ca }
.gv-node.g-chapter circle { fill: #0ea5e9 }
.gv-node.g-concept circle { fill: #6366f1 }
.gv-node.g-method circle { fill: #10b981 }
.gv-node.g-task circle { fill: #f59e0b }
.gv-node.g-hypothesis circle { fill: #ec4899 }
.gv-node.g-project circle { fill: #7c3aed }
.gv-node.g-document circle { fill: #14b8a6 }
.gv-node.g-person circle { fill: #ef4444 }
.gv-label { font-size: 11px; fill: #1f2937; text-anchor: middle; dominant-baseline: middle; pointer-events: none; user-select: none }
.gv-empty, .gv-skeleton { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; color: var(--surface-500, #6b7280); font-size: 13px; position: relative }
.gv-empty-ico { font-size: 36px; opacity: .5 }
.gv-skeleton { min-height: 260px }
.gv-sk-dot { position: absolute; width: 10px; height: 10px; border-radius: 50%; background: var(--surface-300, #cbd5e1);
             animation: gv-pulse 1.4s ease-in-out infinite }
@keyframes gv-pulse { 0%, 100% { opacity: .3; transform: scale(1) } 50% { opacity: 1; transform: scale(1.6) } }
</style>
