<template>
  <div class="rounded-lg border border-surface-200 bg-surface-50/60 dark:bg-surface-800/40">
    <button type="button" @click="open = !open"
            class="w-full flex items-center gap-2 px-3 py-2.5 text-left">
      <span class="text-base">🧩</span>
      <span class="text-sm font-medium">引用系统素材（原资料 · 科学问题 · 研究报告 · 项目对话 · 技能 · 流水线）</span>
      <span v-if="totalSelected"
            class="ml-auto text-[11px] px-2 py-0.5 rounded-full bg-primary-100 text-primary-700 font-medium">
        已选 {{ totalSelected }} 项
      </span>
      <span v-else class="ml-auto text-[11px] px-2 py-0.5 rounded-full bg-surface-200 text-surface-500">可选</span>
      <span class="text-surface-400 text-xs">{{ open ? '▲' : '▼' }}</span>
    </button>

    <div v-if="loading" class="px-3 pb-3 text-xs text-surface-500">⏳ 正在扫描你的素材…</div>

    <div v-else-if="open" class="px-3 pb-3 space-y-2">
      <p class="text-[11px] text-surface-500 leading-relaxed">
        勾选的内容会被拼接成「参考资料」一并交给 AI，让生成的课件 / 更新的内容
        直接建立在你已有的<span class="font-medium">资料、题目、研究报告、对话、流水线产出和技能结果</span>之上。
      </p>

      <div class="flex flex-wrap gap-1.5 border-b border-surface-200 pb-2">
        <button v-for="t in tabs" :key="t.key" type="button"
                @click="tab = t.key"
                :class="['text-[11px] px-2.5 py-1 rounded-full transition-colors',
                         tab === t.key ? 'bg-primary-600 text-white' : 'bg-white text-surface-600 hover:bg-surface-100 border border-surface-200']">
          {{ t.icon }} {{ t.label }}
          <span v-if="countOf(t.key)" class="ml-0.5 opacity-80">({{ countOf(t.key) }})</span>
        </button>
      </div>

      <div class="max-h-52 overflow-y-auto space-y-1 pr-1">
        <div v-if="currentList.length === 0" class="text-xs text-surface-400 py-4 text-center">
          暂无可引用素材（可在对应模块先创建）
        </div>
        <label v-for="it in currentList" :key="it.key"
              class="flex items-start gap-2 px-2 py-1.5 rounded-md hover:bg-white cursor-pointer transition-colors">
          <input type="checkbox" class="mt-0.5 accent-primary-600" :checked="isSelected(it)"
                 @change="toggle(it)" />
          <div class="min-w-0 flex-1">
            <p class="text-xs truncate">{{ it.label }}</p>
            <p v-if="it.sub" class="text-[10px] text-surface-400 truncate">{{ it.sub }}</p>
          </div>
          <span v-if="it.tag" class="text-[10px] px-1.5 py-0.5 rounded bg-surface-200 text-surface-500 flex-shrink-0">{{ it.tag }}</span>
        </label>
      </div>

      <!-- 技能可带输入参数（自主 / git / 网络搜集的 skill 都能跑） -->
      <div v-if="tab === 'skills' && sel.skill_runs.length" class="space-y-2 pt-2 border-t border-surface-200">
        <p class="text-[11px] font-medium text-surface-600">为技能提供运行输入（JSON，可留空）</p>
        <div v-for="s in sel.skill_runs" :key="s.skill_id" class="flex items-start gap-2">
          <span class="text-[11px] mt-1.5 w-32 truncate text-surface-500">{{ labelOf('skills', s.skill_id) }}</span>
          <input v-model="s._raw" class="input-field flex-1 text-[11px] font-mono py-1"
                 placeholder='{"query": "transformer 对齐"}' @blur="syncSkillInput(s)" />
        </div>
      </div>

      <!-- 项目对话：选中项目后自动带出最近对话 -->
      <div v-if="tab === 'projects'" class="pt-2 border-t border-surface-200">
        <label class="flex items-center gap-2 text-[11px] text-surface-600 cursor-pointer">
          <input type="checkbox" v-model="withChat" class="accent-primary-600" />
          同时引用所选项目下的最近 AI 对话记录
        </label>
      </div>

      <div v-if="totalSelected" class="flex items-center justify-between pt-2 border-t border-surface-200">
        <div class="text-[11px] text-surface-500">
          预计注入 {{ approxChars }} 字符上下文
        </div>
        <button type="button" class="text-[11px] text-red-500 hover:underline" @click="clearAll">清空选择</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { courseApi, type MaterialSources, type MaterialSelection } from '@/api/modules/courses'

interface PickItem { key: string; id: any; label: string; sub?: string; tag?: string }

const props = defineProps<{ modelValue?: MaterialSelection | null; preselect?: MaterialSelection | null }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: MaterialSelection): void }>()

const open = ref(false)
const loading = ref(false)
const tab = ref<'documents' | 'questions' | 'tasks' | 'projects' | 'runs' | 'skills'>('documents')
const withChat = ref(false)
const source = ref<MaterialSources>({
  documents: [], questions: [], tasks: [], projects: [], pipelines: [], pipeline_runs: [], skills: [],
})

const sel = reactive<{
  doc_ids: number[]
  question_ids: number[]
  task_ids: number[]
  project_ids: number[]
  pipeline_run_ids: string[]
  skill_runs: { skill_id: string; input_data?: Record<string, any>; _raw?: string }[]
}>({ doc_ids: [], question_ids: [], task_ids: [], project_ids: [], pipeline_run_ids: [], skill_runs: [] })

const tabs = [
  { key: 'documents', icon: '📄', label: '原资料' },
  { key: 'questions', icon: '❓', label: '科学问题' },
  { key: 'tasks', icon: '📑', label: '研究报告' },
  { key: 'projects', icon: '📁', label: '项目/对话' },
  { key: 'runs', icon: '⚡', label: '流水线' },
  { key: 'skills', icon: '🛠️', label: '技能' },
] as const

const lists = computed<Record<string, PickItem[]>>(() => ({
  documents: source.value.documents.map(d => ({
    key: `doc-${d.id}`, id: d.id, label: d.label,
    sub: d.has_content ? `${(d.ext || '').toUpperCase()} · 已解析出文本` : `${(d.ext || '').toUpperCase()} · 暂无文本层`,
  })),
  questions: source.value.questions.map(q => ({
    key: `q-${q.question_id}`, id: q.question_id, label: q.label, sub: q.category,
  })),
  tasks: source.value.tasks.map(t => ({ key: `t-${t.id}`, id: t.id, label: t.label || `研究报告 #${t.id}`, sub: `题号 #${t.question_id}` })),
  projects: source.value.projects.map(p => ({ key: `p-${p.id}`, id: p.id, label: p.label, tag: '含对话' })),
  runs: source.value.pipeline_runs.map(r => ({
    key: `r-${r.id}`, id: r.id, label: r.label, tag: r.status,
  })),
  skills: source.value.skills.map(s => ({
    key: `s-${s.id}`, id: s.id, label: s.label,
    tag: s.type === 'webhook' ? '🌐 外接' : s.type === 'prompt' ? '🧠 自主' : '⚙️ 内置',
  })),
}))

const currentList = computed(() => lists.value[tab.value] || [])

function countOf(key: string) {
  if (key === 'documents') return sel.doc_ids.length
  if (key === 'questions') return sel.question_ids.length
  if (key === 'tasks') return sel.task_ids.length
  if (key === 'projects') return sel.project_ids.length
  if (key === 'runs') return sel.pipeline_run_ids.length
  if (key === 'skills') return sel.skill_runs.length
  return 0
}
const totalSelected = computed(() =>
  sel.doc_ids.length + sel.question_ids.length + sel.task_ids.length +
  sel.project_ids.length + sel.pipeline_run_ids.length + sel.skill_runs.length)
const approxChars = computed(() => totalSelected.value * 1800)

function isSelected(it: PickItem) {
  if (tab.value === 'documents') return sel.doc_ids.includes(it.id)
  if (tab.value === 'questions') return sel.question_ids.includes(it.id)
  if (tab.value === 'tasks') return sel.task_ids.includes(it.id)
  if (tab.value === 'projects') return sel.project_ids.includes(it.id)
  if (tab.value === 'runs') return sel.pipeline_run_ids.includes(it.id)
  if (tab.value === 'skills') return sel.skill_runs.some(s => s.skill_id === it.id)
  return false
}

function toggle(it: PickItem) {
  if (tab.value === 'documents') sel.doc_ids = xor(sel.doc_ids, it.id)
  else if (tab.value === 'questions') sel.question_ids = xor(sel.question_ids, it.id)
  else if (tab.value === 'tasks') sel.task_ids = xor(sel.task_ids, it.id)
  else if (tab.value === 'projects') sel.project_ids = xor(sel.project_ids, it.id)
  else if (tab.value === 'runs') sel.pipeline_run_ids = xor(sel.pipeline_run_ids, it.id)
  else if (tab.value === 'skills') {
    const hit = sel.skill_runs.findIndex(s => s.skill_id === it.id)
    if (hit >= 0) sel.skill_runs.splice(hit, 1)
    else sel.skill_runs.push({ skill_id: it.id, input_data: undefined, _raw: '' })
  }
}

function xor<T>(arr: T[], v: T): T[] {
  return arr.includes(v) ? arr.filter(x => x !== v) : [...arr, v]
}

function labelOf(kind: keyof MaterialSources, id: any) {
  const list = source.value[kind] as any[]
  const hit = list.find(x => String(x.id ?? x.question_id) === String(id))
  return hit?.label || String(id)
}

function syncSkillInput(s: { skill_id: string; input_data?: Record<string, any>; _raw?: string }) {
  const raw = (s._raw || '').trim()
  if (!raw) { s.input_data = undefined; return }
  try { s.input_data = JSON.parse(raw) } catch { s.input_data = { query: raw } }
}

function clearAll() {
  sel.doc_ids = []; sel.question_ids = []; sel.task_ids = []
  sel.project_ids = []; sel.pipeline_run_ids = []; sel.skill_runs = []
  withChat.value = false
}

/** 把内部选择映射为后端 MaterialSelection 契约 */
const payload = computed<MaterialSelection>(() => {
  const out: MaterialSelection = {}
  if (sel.doc_ids.length) out.doc_ids = [...sel.doc_ids]
  if (sel.question_ids.length) out.question_ids = [...sel.question_ids]
  if (sel.task_ids.length) out.task_ids = [...sel.task_ids]
  if (sel.project_ids.length) {
    // 后端按单项目上下文取对话/假设，多选时取最近一个
    out.project_id = sel.project_ids[sel.project_ids.length - 1]
  }
  if (sel.pipeline_run_ids.length) out.pipeline_run_id = sel.pipeline_run_ids[0]
  if (sel.skill_runs.length) {
    out.skill_runs = sel.skill_runs.map(s => ({ skill_id: s.skill_id, ...(s.input_data ? { input_data: s.input_data } : {}) }))
  }
  if (withChat.value && sel.project_ids.length) out.chat_project_id = sel.project_ids[sel.project_ids.length - 1]
  if (sel.pipeline_run_ids.length > 1) out.pipeline_run_ids = [...sel.pipeline_run_ids]
  return out
})

watch([payload], () => emit('update:modelValue', payload.value))

watch(() => props.modelValue, (v) => {
  if (v && (v.doc_ids?.length || v.question_ids?.length)) open.value = true
})

function applyPreselect(p?: MaterialSelection | null) {
  if (!p) return
  if (p.doc_ids?.length) sel.doc_ids = Array.from(new Set([...sel.doc_ids, ...p.doc_ids]))
  if (p.question_ids?.length) sel.question_ids = Array.from(new Set([...sel.question_ids, ...p.question_ids]))
  if (p.task_ids?.length) sel.task_ids = Array.from(new Set([...sel.task_ids, ...p.task_ids]))
  if (p.project_id) sel.project_ids = Array.from(new Set([...sel.project_ids, p.project_id]))
  // 外部要求携带对话（如从 AI 对话页的「📽️ 做成课件」进来）
  if (p.chat_project_id) withChat.value = true
  if (p.pipeline_run_id) sel.pipeline_run_ids = Array.from(new Set([...sel.pipeline_run_ids, p.pipeline_run_id]))
  if (p.skill_runs?.length) {
    for (const s of p.skill_runs) {
      if (!sel.skill_runs.some(x => x.skill_id === s.skill_id)) {
        sel.skill_runs.push({ skill_id: s.skill_id, input_data: s.input_data, _raw: s.input_data ? JSON.stringify(s.input_data) : '' })
      }
    }
    if (p.skill_runs.some(s => s.input_data)) open.value = true
  }
  if (totalSelected.value) open.value = true
}

async function load() {
  const fresh = !source.value.documents.length && !source.value.skills.length
  if (fresh) {
    loading.value = true
    try {
      const res = await courseApi.materials(40)
      source.value = { ...source.value, ...res.data }
      if (source.value.pipeline_runs.length) open.value = true
    } catch (e) {
      console.warn('materials load failed', e)
    } finally { loading.value = false }
  }
  // 跨模块携参进来（例如技能页「用于课件」、题目页「开课」）
  applyPreselect(props.preselect)
}

onMounted(load)
watch(open, (v) => { if (v) load() })
watch(() => props.preselect, (v) => { if (v && Object.keys(v).length) { load(); applyPreselect(v) } }, { deep: true })

defineExpose({ load, clearAll, payload })
</script>
