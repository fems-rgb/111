<template>
  <div class="max-w-6xl mx-auto px-5 py-7">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-surface-900">🗒️ 计划中心</h1>
      <div class="flex items-center gap-2">
        <button class="btn-secondary text-sm" @click="showCreate = true">➕ 新建计划</button>
        <button class="btn-primary text-sm" @click="showAI = true">🤖 AI 生成</button>
      </div>
    </div>

    <!-- 四 tab -->
    <div class="flex gap-1 mb-4 border-b border-surface-200">
      <button v-for="t in tabs" :key="t.key"
              @click="currentTab = t.key; load()"
              :class="[currentTab === t.key ? 'border-primary-500 text-primary-700' : 'border-transparent text-surface-500 hover:text-surface-700', 'px-4 py-2 text-sm font-medium border-b-2 -mb-px']">
        {{ t.label }}
        <span v-if="t.key === currentTab && loading" class="ml-1 text-[10px] text-surface-400">…</span>
      </button>
    </div>

    <!-- 批量管理条：全选 / 删除选中 -->
    <div v-if="!loading && items.length" class="card p-3 mb-3 flex flex-wrap items-center gap-2 text-xs">
      <label class="flex items-center gap-1 cursor-pointer select-none">
        <input type="checkbox" class="rounded border-surface-300" :checked="allSelected"
               :indeterminate="sel.size > 0 && !allSelected" @change="toggleAll" />
        全选（共 {{ items.length }} 个）
      </label>
      <button @click="batchDelete" :disabled="!sel.size || deleting"
              class="px-2.5 py-1 rounded-md bg-red-50 text-red-600 hover:bg-red-100 disabled:opacity-40 disabled:cursor-not-allowed">
        🗑 删除选中{{ sel.size ? ` (${sel.size})` : '' }}
      </button>
    </div>

    <div v-if="loading && !items.length" class="py-16 text-center text-sm text-surface-400">加载中…</div>
    <div v-else-if="!items.length" class="py-16 text-center">
      <p class="text-4xl mb-3">📝</p>
      <p class="text-sm text-surface-500">还没有{{ tabLabel }}计划</p>
      <div class="mt-3 flex gap-2 justify-center">
        <button class="btn-secondary text-xs" @click="showCreate = true">➕ 新建</button>
        <button class="btn-primary text-xs" @click="showAI = true">🤖 AI 生成</button>
      </div>
    </div>

    <div v-else class="space-y-3">
      <div v-for="p in pagedItems" :key="p.id" class="card p-4">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-start gap-2 min-w-0 flex-1">
            <input type="checkbox" class="mt-1 rounded border-surface-300 flex-shrink-0"
                   :checked="sel.has(p.id)" @change="toggle(p.id)" />
            <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 flex-wrap">
              <h3 class="text-base font-semibold text-surface-800 truncate">{{ p.title }}</h3>
              <span class="text-[10px] px-2 py-0.5 rounded-full" :class="sourceClass(p.source)">{{ p.source === 'ai' ? 'AI' : '手动' }}</span>
              <span v-if="p.project_title" class="text-[10px] px-2 py-0.5 rounded-full bg-sky-50 text-sky-700">📌 {{ p.project_title }}</span>
              <span v-if="p.pipeline_id" class="text-[10px] px-2 py-0.5 rounded-full bg-purple-50 text-purple-700">⚙️ 已转流水线</span>
              <span v-if="p.status === 'done'" class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">✓ 完成</span>
            </div>
            <p class="mt-0.5 text-[11px] text-surface-400">
              {{ doneCount(p) }}/{{ p.items.length }} 已完成
              <span v-if="p.due_at">· 到期 {{ fmtDate(p.due_at) }}</span>
              <span v-if="dueSoon(p)" class="text-amber-600 ml-1">⚠ 即将到期</span>
            </p>
            </div>
          </div>
          <div class="flex items-center gap-1 flex-shrink-0">
            <button v-if="canToPipeline(p)" @click="toPipeline(p)" :disabled="busy === p.id"
                    class="text-xs px-2.5 py-1 rounded-md bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50">
              {{ busy === p.id ? '处理中…' : '转流水线' }}
            </button>
            <button v-if="p.pipeline_id" @click="goPipeline(p.pipeline_id)"
                    class="text-xs px-2.5 py-1 rounded-md border border-purple-200 text-purple-700 hover:bg-purple-50">
              执行
            </button>
            <button @click="removePlan(p)" class="text-xs px-2 py-1 rounded-md text-red-600 hover:bg-red-50">🗑</button>
          </div>
        </div>

        <!-- items -->
        <div class="mt-3 space-y-1.5">
          <div v-for="(it, i) in p.items" :key="i"
               class="flex items-center gap-2 p-2 rounded-lg hover:bg-surface-50">
            <input type="checkbox" :checked="!!it.done" @change="toggleItem(p, i)"
                   class="rounded border-surface-300 w-4 h-4 flex-shrink-0" />
            <div class="min-w-0 flex-1">
              <p class="text-sm truncate" :class="it.done ? 'text-surface-400 line-through' : 'text-surface-700'">{{ it.text }}</p>
              <p v-if="it.due || it.agent" class="text-[11px] text-surface-400">
                <span v-if="it.due">🗓 {{ it.due }}</span>
                <span v-if="it.agent" class="ml-2 px-1.5 py-0.5 rounded bg-surface-100 font-mono">{{ it.agent }}</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页：页码 + 翻页 -->
    <div v-if="!loading && pages > 1" class="flex items-center justify-center gap-3 mt-4 text-sm">
      <button @click="page = Math.max(1, page - 1)" :disabled="page <= 1"
              class="px-3 py-1.5 rounded-lg border border-surface-200 hover:bg-surface-100 disabled:opacity-40">◀ 上一页</button>
      <span class="text-surface-500">第 {{ page }} / {{ pages }} 页 · 共 {{ items.length }} 个</span>
      <button @click="page = Math.min(pages, page + 1)" :disabled="page >= pages"
              class="px-3 py-1.5 rounded-lg border border-surface-200 hover:bg-surface-100 disabled:opacity-40">下一页 ▶</button>
    </div>
    <Teleport to="body">
      <div v-if="showCreate" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="showCreate = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div class="px-6 py-4 border-b border-surface-200 flex justify-between items-center">
            <h3 class="font-semibold">➕ 新建{{ tabLabel }}计划</h3>
            <button @click="showCreate = false" class="text-surface-400 text-xl">&times;</button>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">标题</label>
              <input v-model="createForm.title" class="input-field" placeholder="例如：本周论文修订" />
            </div>
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">所属项目（team/pipeline 场景）</label>
              <select v-model.number="createForm.project_id" class="input-field">
                <option :value="0">不关联</option>
                <option v-for="pj in projects" :key="pj.id" :value="pj.id">{{ pj.title }}</option>
              </select>
            </div>
            <div class="flex items-center gap-3">
              <label class="block text-xs font-medium text-surface-600">范围</label>
              <select v-model="createForm.scope" class="input-field text-sm">
                <option value="personal">个人</option>
                <option value="team">团队（项目内共享）</option>
                <option value="pipeline">流水线（可执行）</option>
                <option value="auto">AI 自主</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">到期日（可选）</label>
              <input v-model="createForm.due_at" type="date" class="input-field" />
            </div>
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-2">步骤</label>
              <div class="space-y-2">
                <div v-for="(it, i) in createForm.items" :key="i" class="flex items-center gap-2">
                  <input v-model="it.text" class="input-field flex-1" placeholder="步骤描述" />
                  <input v-if="createForm.scope === 'pipeline'" v-model="it.agent" class="input-field w-32" placeholder="agent" />
                  <button @click="createForm.items.splice(i, 1)" class="text-red-500 text-sm w-6">×</button>
                </div>
                <button @click="createForm.items.push({ text: '', agent: '' })" class="text-xs text-primary-600 hover:underline">➕ 添加一步</button>
              </div>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-surface-200 flex justify-end gap-2">
            <button @click="showCreate = false" class="btn-secondary text-sm">取消</button>
            <button @click="submitCreate" class="btn-primary text-sm" :disabled="!createForm.title || creating">
              {{ creating ? '创建中…' : '创建' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══ AI 生成计划 ═══ -->
    <Teleport to="body">
      <div v-if="showAI" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="showAI = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div class="px-6 py-4 border-b border-surface-200 flex justify-between items-center">
            <h3 class="font-semibold">🤖 AI 生成{{ tabLabel }}计划</h3>
            <button @click="showAI = false" class="text-surface-400 text-xl">&times;</button>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">范围</label>
              <select v-model="aiForm.scope" class="input-field text-sm">
                <option value="personal">个人</option>
                <option value="team">团队（项目内共享）</option>
                <option value="pipeline">流水线（可执行）</option>
                <option value="auto">AI 自主</option>
              </select>
            </div>
            <div v-if="aiForm.scope === 'team' || aiForm.scope === 'pipeline'">
              <label class="block text-xs font-medium text-surface-600 mb-1">关联项目</label>
              <select v-model.number="aiForm.project_id" class="input-field">
                <option :value="0">不关联</option>
                <option v-for="pj in projects" :key="pj.id" :value="pj.id">{{ pj.title }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-surface-600 mb-1">主题</label>
              <textarea v-model="aiForm.topic" class="input-field h-20" placeholder="例如：把「Transformer 视觉应用」开成一门 8 章的研讨课"></textarea>
            </div>
            <!-- 预览 & 编辑 -->
            <div v-if="aiPreview.length">
              <p class="text-xs font-medium text-surface-600 mb-2">预览（可逐条编辑）</p>
              <div class="space-y-2">
                <div v-for="(it, i) in aiPreview" :key="i" class="flex items-center gap-2">
                  <input v-model="it.text" class="input-field flex-1" />
                  <input v-if="aiForm.scope === 'pipeline'" v-model="it.agent" class="input-field w-32" placeholder="agent" />
                  <button @click="aiPreview.splice(i, 1)" class="text-red-500 text-sm w-6">×</button>
                </div>
              </div>
            </div>
            <p v-if="aiError" class="text-xs text-red-600">{{ aiError }}</p>
          </div>
          <div class="px-6 py-4 border-t border-surface-200 flex justify-end gap-2">
            <button @click="showAI = false" class="btn-secondary text-sm">取消</button>
            <button v-if="!aiPreview.length" @click="runAI" class="btn-primary text-sm" :disabled="!aiForm.topic || aiGenerating">
              {{ aiGenerating ? 'AI 生成中…' : '让 AI 拆解' }}
            </button>
            <button v-else @click="saveAIPlan" class="btn-primary text-sm" :disabled="!aiPreview.some(x => x.text)">
              {{ (aiForm.scope === 'pipeline' || aiForm.scope === 'team') ? '保存并准备执行' : '保存计划' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { plansApi, type Plan, type PlanScope } from '@/api/modules/plans'
import { projectApi } from '@/api/modules/project'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const appStore = useAppStore()

const tabs: { key: PlanScope; label: string }[] = [
  { key: 'personal', label: '个人' },
  { key: 'team', label: '团队' },
  { key: 'pipeline', label: '流水线' },
  { key: 'auto', label: 'AI 自主' },
]
const currentTab = ref<PlanScope>('personal')
const tabLabel = computed(() => tabs.find(t => t.key === currentTab.value)?.label || '')

const items = ref<Plan[]>([])
const loading = ref(false)
const busy = ref<number | null>(null)
const projects = ref<Array<{ id: number; title: string }>>([])
// 多选 + 分页 + 批量删除
const sel = ref(new Set<number>())
const deleting = ref(false)
const PAGE_SIZE = 10
const page = ref(1)
const pages = computed(() => Math.max(1, Math.ceil(items.value.length / PAGE_SIZE)))
const pagedItems = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return items.value.slice(start, start + PAGE_SIZE)
})
const allSelected = computed(() =>
  items.value.length > 0 && items.value.every(p => sel.value.has(p.id)))
function toggle(id: number) {
  const s = new Set(sel.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  sel.value = s
}
function toggleAll() {
  sel.value = allSelected.value ? new Set<number>() : new Set(items.value.map(p => p.id))
}
async function batchDelete() {
  const ids = [...sel.value]
  if (!ids.length) return
  if (!confirm(`确定删除选中的 ${ids.length} 个计划？不可恢复。`)) return
  deleting.value = true
  try {
    for (const id of ids) { try { await plansApi.remove(id) } catch { /* 单条失败不中断 */ } }
    appStore.showToast?.(`已删除 ${ids.length} 个计划`, 'success')
    sel.value = new Set()
    page.value = 1
    await load()
  } finally { deleting.value = false }
}

async function load() {
  loading.value = true
  try {
    const r = await plansApi.list(currentTab.value)
    items.value = r.data?.items || []
    sel.value = new Set()
    page.value = 1
  } catch (e: any) {
    appStore.showToast?.('加载计划失败：' + (e?.message || e), 'error')
  } finally { loading.value = false }
}

async function loadProjects() {
  try {
    const r = await projectApi.list()
    projects.value = (r.data || []).map((p: any) => ({ id: p.id, title: p.title }))
  } catch { projects.value = [] }
}

// ═══ 新建 ═══
const showCreate = ref(false)
const creating = ref(false)
const createForm = reactive<{ title: string; scope: PlanScope; project_id: number; due_at: string; items: { text: string; agent?: string }[] }>({
  title: '', scope: 'personal', project_id: 0, due_at: '', items: [{ text: '' }],
})

async function submitCreate() {
  if (!createForm.title) return
  creating.value = true
  try {
    await plansApi.create({
      title: createForm.title,
      scope: createForm.scope,
      project_id: createForm.project_id || null,
      due_at: createForm.due_at || null,
      items: createForm.items.filter(x => x.text.trim()).map(x => ({
        text: x.text, agent: x.agent || '', done: false,
      })),
    })
    showCreate.value = false
    createForm.title = ''; createForm.items = [{ text: '' }]; createForm.due_at = ''
    appStore.showToast?.('计划已创建', 'success')
    currentTab.value = createForm.scope
    await load()
  } catch (e: any) {
    appStore.showToast?.('创建失败：' + (e?.response?.data?.detail || e?.message || e), 'error')
  } finally { creating.value = false }
}

// ═══ AI 生成 ═══
const showAI = ref(false)
const aiGenerating = ref(false)
const aiError = ref('')
const aiForm = reactive<{ topic: string; scope: PlanScope; project_id: number }>({
  topic: '', scope: 'personal', project_id: 0,
})
const aiPreview = ref<{ text: string; agent: string; due: string }[]>([])

async function runAI() {
  if (!aiForm.topic) return
  aiGenerating.value = true; aiError.value = ''; aiPreview.value = []
  try {
    const r = await plansApi.ai({
      topic: aiForm.topic, scope: aiForm.scope,
      project_id: aiForm.project_id || null,
      model: appStore.preferredModel || undefined,
    })
    aiPreview.value = (r.data?.plan?.items || []).map(it => ({
      text: it.text || '', agent: it.agent || '', due: it.due || '',
    }))
  } catch (e: any) {
    aiError.value = e?.response?.data?.detail || e?.message || String(e)
  } finally { aiGenerating.value = false }
}

async function saveAIPlan() {
  const cleaned = aiPreview.value.filter(x => x.text.trim())
  if (!cleaned.length) return
  aiGenerating.value = true
  try {
    const r = await plansApi.create({
      title: aiForm.topic.slice(0, 40),
      scope: aiForm.scope,
      project_id: aiForm.project_id || null,
      items: cleaned.map(x => ({ text: x.text, agent: x.agent, due: x.due, done: false })),
    })
    // 保存后，若为 pipeline/team 自动转流水线
    if ((aiForm.scope === 'pipeline' || aiForm.scope === 'team') && cleaned.some(x => x.agent)) {
      try { await plansApi.toPipeline(r.data.plan.id) } catch { /* 可容忍：手动再点 */ }
    }
    showAI.value = false; aiForm.topic = ''; aiPreview.value = []
    currentTab.value = aiForm.scope
    appStore.showToast?.('AI 计划已保存', 'success')
    await load()
  } catch (e: any) {
    aiError.value = e?.response?.data?.detail || String(e)
  } finally { aiGenerating.value = false }
}

// ═══ 操作 ═══
function canToPipeline(p: Plan) {
  return !p.pipeline_id && (p.items || []).filter(i => i.agent).length >= 2
}
async function toPipeline(p: Plan) {
  busy.value = p.id
  try {
    const r = await plansApi.toPipeline(p.id)
    p.pipeline_id = r.data.pipeline_id
    appStore.showToast?.(`已转流水线（${r.data.steps_count} 步）`, 'success')
    await load()
  } catch (e: any) {
    appStore.showToast?.('转流水线失败：' + (e?.response?.data?.detail || e?.message || e), 'error')
  } finally { busy.value = null }
}
function goPipeline(pid: string) { router.push(`/automation?pipelineId=${pid}`) }

async function toggleItem(p: Plan, i: number) {
  p.items[i].done = !p.items[i].done
  try { await plansApi.update(p.id, { items: p.items }) } catch { /* revert */ p.items[i].done = !p.items[i]!.done }
}

async function removePlan(p: Plan) {
  if (!confirm(`删除计划「${p.title}」？`)) return
  try { await plansApi.remove(p.id); await load() } catch (e: any) {
    appStore.showToast?.('删除失败：' + (e?.response?.data?.detail || e?.message || e), 'error')
  }
}

function doneCount(p: Plan) { return (p.items || []).filter(i => i.done).length }
function fmtDate(iso: string) { return (iso || '').slice(0, 10) }
function dueSoon(p: Plan) {
  if (!p.due_at || p.status === 'done') return false
  const d = new Date(p.due_at).getTime() - Date.now()
  return d < 3 * 86400_000
}
function sourceClass(src: string) {
  return src === 'ai' ? 'bg-purple-50 text-purple-700' : 'bg-surface-100 text-surface-600'
}

onMounted(async () => { await Promise.all([load(), loadProjects()]) })
</script>
