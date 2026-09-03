<template>
  <div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-surface-800">⚙️ 自动化流水线</h1>
      <button class="btn-primary text-sm" @click="showCreate = true">+ 新建 Pipeline</button>
    </div>

    <!-- Tab：定时任务 / 运行记录 -->
    <div class="flex gap-2 border-b border-surface-200">
      <button v-for="t in tabs" :key="t.key" @click="activeTab = t.key"
        :class="['px-4 py-2 text-sm font-medium border-b-2 transition', activeTab===t.key ? 'border-primary-500 text-primary-600' : 'border-transparent text-surface-500']">
        {{ t.icon }} {{ t.label }}
      </button>
    </div>

    <!-- ===== 模版画廊（对标 WorkBuddy）===== -->
    <div v-if="activeTab==='templates'">
      <h2 class="text-lg font-semibold mb-3">🧩 自动化任务模版</h2>
      <div v-if="templates.length===0" class="card p-8 text-center text-surface-400">加载模版中...</div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="tpl in templates" :key="tpl.id" @click="openFromTemplate(tpl)"
          class="card p-5 cursor-pointer hover:ring-2 ring-primary-300 hover:-translate-y-0.5 transition-all">
          <div class="flex items-center gap-3 mb-2">
            <span class="text-2xl">{{ tpl.icon }}</span>
            <h3 class="font-semibold">{{ tpl.name }}</h3>
          </div>
          <p class="text-xs text-surface-500 mb-3 line-clamp-2">{{ tpl.description }}</p>
          <div class="flex items-center justify-between text-xs text-surface-400">
            <span>{{ tpl.steps?.length || 0 }} 个步骤</span>
            <span class="text-primary-600 font-medium">使用模版 →</span>
          </div>
        </div>
      </div>

      <!-- 我的流水线 -->
      <h2 class="text-lg font-semibold mt-8 mb-3">📋 我的流水线</h2>
      <div v-if="loading" class="card p-8 text-center text-surface-400">加载中...</div>
      <div v-else-if="pipelines.length===0" class="card p-8 text-center text-surface-400">
        <span class="text-3xl block mb-2">⚙️</span>
        <p>开启你的第一个自动化任务吧 —— 从上方模版一键创建</p>
      </div>
      <div v-else class="space-y-4">
        <div v-for="p in pipelines" :key="p.id" class="card p-5 hover:ring-2 ring-primary-200 transition-all">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <span class="text-xl">⚙️</span>
              <div>
                <h3 class="font-semibold">{{ p.name }}</h3>
                <p class="text-xs text-surface-500">{{ p.description || '无描述' }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span :class="['px-2 py-0.5 rounded-full text-xs font-medium', statusClass(p.status)]">{{ statusLabel(p.status) }}</span>
              <button @click="openEditor(p)" class="btn-secondary text-xs px-3 py-1">✏️ 编辑</button>
              <button @click="runPipeline(p.id)" :disabled="p.status==='running'" class="btn-primary text-xs px-3 py-1">▶ 运行</button>
              <button @click="viewLogs(p)" class="btn-secondary text-xs px-3 py-1">📊 日志</button>
              <button @click="deletePipeline(p.id)" class="btn-secondary text-xs px-3 py-1 text-red-600">删除</button>
            </div>
          </div>
          <div class="flex items-center gap-4 text-xs text-surface-400">
            <span>触发: {{ triggerLabel(p.trigger) }}</span>
            <span>步骤: {{ p.steps?.length || 0 }}</span>
            <span>运行次数: {{ p.run_count }}</span>
            <span v-if="p.last_run">上次: {{ new Date(p.last_run).toLocaleString('zh-CN') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 运行记录 Tab ===== -->
    <div v-if="activeTab==='runs'">
      <h2 class="text-lg font-semibold mb-3">📈 运行记录</h2>
      <div v-if="allRuns.length===0" class="card p-8 text-center text-surface-400">暂无运行记录，运行一条流水线后将在此显示</div>
      <div v-else class="space-y-3">
        <div v-for="r in allRuns" :key="r.run_id" class="card p-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium">{{ r.pipeline_name || r.pipeline_id }} · Run #{{ r.run_id }}</span>
            <span :class="runStatusClass(r.status)" class="text-xs font-medium px-2 py-0.5 rounded-full">{{ runStatusLabel(r.status) }}</span>
          </div>
          <div class="text-xs text-surface-400 mb-2">{{ fmtTime(r.started_at) }} → {{ fmtTime(r.finished_at) }}</div>
          <div class="space-y-1">
            <div v-for="step in (r.steps||[])" :key="step.step" class="flex items-center gap-2 text-xs">
              <span class="w-5 h-5 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold">{{ step.step }}</span>
              <span class="w-24">{{ step.agent }}</span>
              <span :class="stepStatusClass(step.status)">{{ stepStatusLabel(step.status) }}</span>
              <span class="text-surface-400">{{ step.duration_ms }}ms</span>
              <span v-if="step.tokens" class="text-surface-400">· {{ step.tokens }} tokens</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 从模版创建弹窗（名称/提示词/参数/连接器/频率/权限确认，对标WorkBuddy）===== -->
    <Teleport to="body">
      <div v-if="tplModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="tplModal=null">
        <div class="bg-white rounded-2xl shadow-2xl w-[560px] max-h-[85vh] overflow-auto p-6 space-y-4">
          <h3 class="text-lg font-semibold">{{ tplModal.icon }} 从模版创建 · {{ tplModal.name }}</h3>
          <div><label class="text-xs text-surface-500">名称</label>
            <input v-model="tplForm.name" class="input-field mt-1" :placeholder="tplModal.name" /></div>
          <div v-for="f in (tplModal.params_schema||[])" :key="f.key">
            <label class="text-xs text-surface-500">{{ f.label }} <span v-if="f.required" class="text-red-500">*</span></label>
            <textarea v-if="f.type==='textarea'" v-model="tplForm.params[f.key]" class="input-field mt-1 h-24 resize-none" :placeholder="f.placeholder"></textarea>
            <select v-else-if="f.type==='select'" v-model="tplForm.params[f.key]" class="input-field mt-1">
              <option v-for="o in f.options" :key="o.value" :value="o.value">{{ o.label }}</option>
            </select>
            <input v-else v-model="tplForm.params[f.key]" class="input-field mt-1" :placeholder="f.placeholder" />
          </div>
          <div><label class="text-xs text-surface-500">执行频率</label>
            <div class="flex gap-2 mt-1">
              <button v-for="tr in [{k:'manual',l:'手动'},{k:'scheduled',l:'周期'},{k:'webhook',l:'单次/Webhook'}]" :key="tr.k"
                @click="tplForm.trigger=tr.k" :class="['px-3 py-1 rounded-lg text-sm border', tplForm.trigger===tr.k?'border-primary-500 bg-primary-50 text-primary-600':'border-surface-200']">{{ tr.l }}</button>
            </div>
          </div>
          <div v-if="tplForm.trigger==='scheduled'"><label class="text-xs text-surface-500">Cron 表达式</label>
            <input v-model="tplForm.cron" class="input-field mt-1" placeholder="0 9 * * *  (每天9点)" /></div>
          <!-- 权限确认（对标 WorkBuddy 完全访问权限弹窗）-->
          <label class="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-800">
            <input type="checkbox" v-model="tplForm.ack" class="mt-0.5" />
            <span>⚠️ 此流水线将以完全访问权限运行：可读写工作空间文件、调用已授权连接器、执行代码与网络请求。我已了解风险并愿意为执行结果负责。</span>
          </label>
          <div class="flex justify-end gap-3 pt-2">
            <button @click="tplModal=null" class="btn-secondary">取消</button>
            <button @click="confirmFromTemplate" :disabled="!tplForm.ack || creating" class="btn-primary">{{ creating?'创建中...':'确认创建' }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 空白新建弹窗（升级版：与模版创建体验对齐） -->
    <Teleport to="body">
      <div v-if="showCreate" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showCreate=false">
        <div class="bg-white rounded-2xl shadow-2xl w-[560px] max-h-[85vh] overflow-auto p-6 space-y-4">
          <h3 class="text-lg font-semibold"> 新建自定义流水线</h3>
          <div><label class="text-xs text-surface-500">名称 <span class="text-red-500">*</span></label>
            <input v-model="newPipeline.name" class="input-field mt-1" placeholder="给流水线起个名字" /></div>
          <div><label class="text-xs text-surface-500">描述</label>
            <textarea v-model="newPipeline.description" class="input-field mt-1 h-20 resize-none" placeholder="简要描述这条流水线的用途..." /></div>

          <!-- 初始步骤配置 -->
          <div>
            <label class="text-xs text-surface-500 mb-2 block">执行步骤（可稍后在编辑中添加）</label>
            <div v-for="(s,idx) in newPipeline.steps" :key="idx" class="flex items-center gap-2 p-3 mb-2 bg-surface-50 rounded-lg border border-surface-200">
              <span class="w-6 h-6 rounded-full bg-primary-100 text-primary-700 text-xs font-bold flex items-center justify-center">{{ idx+1 }}</span>
              <select v-model="s.agent_name" class="flex-1 input-field text-sm py-1">
                <option v-for="a in agentOptions" :key="a.value" :value="a.value">{{ a.label }}</option>
              </select>
              <input v-model="s.params" class="input-field text-xs py-1 w-28" placeholder="参数(可选)" />
              <button class="text-red-500 hover:text-red-700 text-sm" @click="newPipeline.steps.splice(idx,1)">✕</button>
            </div>
            <button @click="newPipeline.steps.push({agent_name:'literature',name:'',params:''})" class="w-full py-2 border-2 border-dashed border-surface-300 rounded-lg text-surface-500 text-sm hover:border-primary-400 hover:text-primary-600">+ 添加步骤</button>
          </div>

          <!-- 执行频率（与模版创建一致的按钮组） -->
          <div><label class="text-xs text-surface-500">执行频率</label>
            <div class="flex gap-2 mt-1">
              <button v-for="tr in [{k:'manual',l:'手动'},{k:'scheduled',l:'周期'},{k:'webhook',l:'单次/Webhook'}]" :key="tr.k"
                @click="newPipeline.trigger=tr.k" :class="['px-3 py-1 rounded-lg text-sm border', newPipeline.trigger===tr.k?'border-primary-500 bg-primary-50 text-primary-600':'border-surface-200']">{{ tr.l }}</button>
            </div>
          </div>
          <div v-if="newPipeline.trigger==='scheduled'"><label class="text-xs text-surface-500">Cron 表达式</label>
            <input v-model="newPipeline.cron" class="input-field mt-1" placeholder="0 9 * * *  (每天9点)" /></div>

          <!-- 权限确认 -->
          <label class="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-800">
            <input type="checkbox" v-model="newPipeline.ack" class="mt-0.5" />
            <span>⚠️ 此流水线将以完全访问权限运行：可读写工作空间文件、调用已授权连接器、执行代码与网络请求。我已了解风险并愿意为执行结果负责。</span>
          </label>

          <div class="flex justify-end gap-3 pt-2">
            <button @click="showCreate=false" class="btn-secondary">取消</button>
            <button @click="createPipeline" :disabled="creating || !newPipeline.ack" class="btn-primary">{{ creating?'创建中...':'确认创建' }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 日志弹窗 -->
    <Teleport to="body">
      <div v-if="logPipeline" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="logPipeline=null">
        <div class="bg-white rounded-2xl shadow-2xl w-[700px] max-h-[80vh] flex flex-col overflow-hidden">
          <div class="flex items-center justify-between px-6 py-4 border-b border-surface-200">
            <h3 class="font-semibold">📊 {{ logPipeline.name }} - 执行日志</h3>
            <button class="text-surface-400 hover:text-surface-700 text-xl" @click="logPipeline=null">&times;</button>
          </div>
          <div class="flex-1 overflow-auto p-6">
            <div v-if="logsLoading" class="text-center text-surface-400">加载中...</div>
            <div v-else-if="pipelineLogs.length===0" class="text-center text-surface-400">暂无执行记录</div>
            <div v-else class="space-y-4">
              <div v-for="(log,li) in pipelineLogs" :key="li" class="border border-surface-200 rounded-lg p-4">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm font-medium">Run #{{ log.run_id }}</span>
                  <span :class="runStatusClass(log.status)" class="text-xs font-medium px-2 py-0.5 rounded-full">{{ runStatusLabel(log.status) }}</span>
                </div>
                <div class="text-xs text-surface-400 mb-2">{{ fmtTime(log.started_at) }} → {{ fmtTime(log.finished_at) }}</div>
                <div class="space-y-1">
                  <div v-for="step in (log.steps||[])" :key="step.step" class="flex items-center gap-2 text-xs">
                    <span class="w-5 h-5 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold">{{ step.step }}</span>
                    <span class="w-24">{{ step.agent }}</span>
                    <span :class="stepStatusClass(step.status)">{{ stepStatusLabel(step.status) }}</span>
                    <span class="text-surface-400">{{ step.duration_ms }}ms</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 步骤编辑弹窗（升级为居中弹窗，与模版创建体验对齐） -->
    <Teleport to="body">
      <div v-if="editingPipeline" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="editingPipeline=null">
        <div class="bg-white rounded-2xl shadow-2xl w-[560px] max-h-[85vh] overflow-auto p-6 space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold">✏️ 编辑流水线 · {{ editingPipeline.name }}</h3>
            <button class="text-surface-400 hover:text-surface-700 text-xl" @click="editingPipeline=null">&times;</button>
          </div>
          <div><label class="text-xs text-surface-500">名称</label><input v-model="editForm.name" class="input-field mt-1" /></div>
          <div><label class="text-xs text-surface-500">描述</label><textarea v-model="editForm.description" class="input-field mt-1 h-16 resize-none" /></div>
          <div>
            <label class="text-xs text-surface-500 mb-2 block">执行步骤（拖拽 ☰ 排序）</label>
            <div v-if="editForm.steps.length===0" class="text-center text-surface-400 text-sm py-4 bg-surface-50 rounded-lg border border-dashed border-surface-300 mb-2">
              暂无步骤，点击下方按钮添加
            </div>
            <div v-for="(s,idx) in editForm.steps" :key="idx" class="flex items-center gap-2 p-3 mb-2 bg-surface-50 rounded-lg border border-surface-200" draggable="true" @dragstart="stepDragIdx=idx" @dragover.prevent @drop="onStepDrop(idx)">
              <span class="cursor-grab text-surface-400">☰</span>
              <span class="w-6 h-6 rounded-full bg-primary-100 text-primary-700 text-xs font-bold flex items-center justify-center">{{ idx+1 }}</span>
              <select v-model="s.agent_name" class="flex-1 input-field text-sm py-1">
                <option v-for="a in agentOptions" :key="a.value" :value="a.value">{{ a.label }}</option>
              </select>
              <input v-model="s.params" class="input-field text-xs py-1 w-28" placeholder="参数(可选)" />
              <button class="text-red-500 hover:text-red-700 text-sm" @click="editForm.steps.splice(idx,1)">✕</button>
            </div>
            <button @click="editForm.steps.push({agent_name:'literature',name:'',params:''})" class="w-full py-2 border-2 border-dashed border-surface-300 rounded-lg text-surface-500 text-sm hover:border-primary-400 hover:text-primary-600">+ 添加步骤</button>
          </div>

          <!-- 执行频率（按钮组，与模版创建一致） -->
          <div><label class="text-xs text-surface-500">执行频率</label>
            <div class="flex gap-2 mt-1">
              <button v-for="tr in [{k:'manual',l:'手动'},{k:'scheduled',l:'周期'},{k:'webhook',l:'单次/Webhook'}]" :key="tr.k"
                @click="editForm.trigger=tr.k" :class="['px-3 py-1 rounded-lg text-sm border', editForm.trigger===tr.k?'border-primary-500 bg-primary-50 text-primary-600':'border-surface-200']">{{ tr.l }}</button>
            </div>
          </div>
          <div v-if="editForm.trigger==='scheduled'"><label class="text-xs text-surface-500">Cron 表达式</label>
            <input v-model="editForm.cron" class="input-field mt-1" placeholder="0 9 * * *  (每天9点)" /></div>

          <!-- 权限提示 -->
          <label class="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-800">
            <input type="checkbox" v-model="editForm.ack" class="mt-0.5" checked />
            <span>⚠️ 此流水线将以完全访问权限运行：可读写工作空间文件、调用已授权连接器、执行代码与网络请求。我已了解风险并愿意为执行结果负责。</span>
          </label>

          <div class="flex justify-end gap-3 pt-2">
            <button @click="editingPipeline=null" class="btn-secondary">取消</button>
            <button @click="saveSteps" :disabled="saving" class="btn-primary">{{ saving?'保存中...':'💾 保存' }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, onUnmounted } from 'vue'
import { automationApi, type Pipeline } from '@/api/modules/automation'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const pipelines = ref<Pipeline[]>([])
const templates = ref<any[]>([])
const loading = ref(false)
const showCreate = ref(false)
const creating = ref(false)
const newPipeline = reactive({ name: '', description: '', trigger: 'manual', steps: [] as any[], cron: '', ack: false })

const tabs = [{ key: 'templates', icon: '⏰', label: '定时任务' }, { key: 'runs', icon: '📈', label: '运行记录' }]
const activeTab = ref('templates')

const logPipeline = ref<Pipeline | null>(null)
const pipelineLogs = ref<any[]>([])
const logsLoading = ref(false)
const allRuns = ref<any[]>([])
let logPollTimer: ReturnType<typeof setInterval> | null = null

const tplModal = ref<any>(null)
const tplForm = reactive<{ name: string; params: Record<string, string>; trigger: string; cron: string; ack: boolean }>({ name: '', params: {}, trigger: 'manual', cron: '', ack: false })

const statusClass = (s: string) => ({ running: 'bg-yellow-100 text-yellow-700', idle: 'bg-green-100 text-green-700', completed: 'bg-blue-100 text-blue-700', failed: 'bg-red-100 text-red-700' }[s] || 'bg-gray-100 text-gray-600')
const statusLabel = (s: string) => ({ running: '运行中', idle: '空闲', completed: '已完成', failed: '失败' }[s] || s)
const runStatusClass = (s: string) => ({ completed: 'bg-green-100 text-green-700', running: 'bg-yellow-100 text-yellow-700', failed: 'bg-red-100 text-red-700', cancelled: 'bg-gray-100 text-gray-600' }[s] || 'bg-gray-100 text-gray-600')
const runStatusLabel = (s: string) => ({ completed: '已完成', running: '运行中', failed: '失败', cancelled: '已取消' }[s] || s)
const stepStatusClass = (s: string) => ({ completed: 'text-green-600', running: 'text-yellow-600 animate-pulse', failed: 'text-red-600', cancelled: 'text-gray-500' }[s] || 'text-surface-400')
const stepStatusLabel = (s: string) => ({ completed: '✓ 完成', running: '◌ 执行中', failed: '✕ 失败', cancelled: '已取消' }[s] || s)
const triggerLabel = (t: string) => ({ manual: '手动', scheduled: '定时', webhook: 'Webhook' }[t] || t)
const fmtTime = (t?: string) => t ? new Date(t).toLocaleString('zh-CN') : '...'

async function loadPipelines() {
  loading.value = true
  try { pipelines.value = (await automationApi.list()).data.pipelines || [] }
  catch { appStore.showToast('加载流水线失败', 'error') }
  finally { loading.value = false }
}
async function loadTemplates() {
  try { templates.value = (await automationApi.templates()).data.templates || [] }
  catch { templates.value = [] }
}
async function loadAllRuns() {
  const runs: any[] = []
  for (const p of pipelines.value) {
    try {
      const logs = (await automationApi.logs(p.id)).data.logs || []
      logs.forEach((r: any) => runs.push({ ...r, pipeline_name: p.name }))
    } catch { /* skip */ }
  }
  runs.sort((a, b) => (b.started_at || '').localeCompare(a.started_at || ''))
  allRuns.value = runs
}
watch(activeTab, (v) => { if (v === 'runs') loadAllRuns() })

function openFromTemplate(tpl: any) {
  tplModal.value = tpl
  const initParams: Record<string, string> = {}
  ;(tpl.params_schema || []).forEach((f: any) => { initParams[f.key] = f.default ?? '' })
  Object.assign(tplForm, { name: tpl.name, params: initParams, trigger: 'manual', cron: '', ack: false })
}
async function confirmFromTemplate() {
  if (!tplModal.value) return
  creating.value = true
  try {
    await automationApi.fromTemplate(tplModal.value.id, tplForm.params)
    appStore.showToast('✅ 已从模版创建流水线', 'success')
    tplModal.value = null
    await loadPipelines()
  } catch (e: any) { appStore.showToast('创建失败: ' + (e.response?.data?.detail || e.message), 'error') }
  finally { creating.value = false }
}
async function createPipeline() {
  if (!newPipeline.name.trim()) { appStore.showToast('请输入名称', 'error'); return }
  creating.value = true
  try {
    await automationApi.create({
      name: newPipeline.name,
      description: newPipeline.description,
      trigger: newPipeline.trigger,
      schedule_cron: newPipeline.cron || undefined,
      steps: newPipeline.steps.map(s => ({ agent_name: s.agent_name, name: s.agent_name, params: s.params || '', research_question: s.params || '' })),
    })
    appStore.showToast('✅ 流水线已创建', 'success'); showCreate.value = false
    Object.assign(newPipeline, { name: '', description: '', trigger: 'manual', steps: [], cron: '', ack: false })
    await loadPipelines()
  } catch (e: any) { appStore.showToast('创建失败: ' + (e.response?.data?.detail || e.message), 'error') }
  finally { creating.value = false }
}
async function runPipeline(id: string) {
  try {
    const res = await automationApi.run(id)
    appStore.showToast('🚀 流水线已启动', 'success')
    await loadPipelines()
    const p = pipelines.value.find(x => x.id === id)
    if (p) { logPipeline.value = p; pipelineLogs.value = [res.data.log].filter(Boolean); startLogPolling(id) }
  } catch (e: any) { appStore.showToast('执行失败: ' + (e.response?.data?.detail || e.message), 'error') }
}
async function viewLogs(p: Pipeline) {
  logPipeline.value = p; logsLoading.value = true; pipelineLogs.value = []
  try {
    const res = await automationApi.logs(p.id); pipelineLogs.value = res.data.logs || []
    const latest = pipelineLogs.value[0]
    if (latest && latest.status === 'running') startLogPolling(p.id)
  } catch { appStore.showToast('加载日志失败', 'error') }
  finally { logsLoading.value = false }
}
async function deletePipeline(id: string) {
  if (!confirm('确定删除该流水线？')) return
  try { await automationApi.delete(id); appStore.showToast('🗑️ 已删除', 'success'); await loadPipelines() }
  catch { appStore.showToast('删除失败', 'error') }
}
function stopLogPolling() { if (logPollTimer) { clearInterval(logPollTimer); logPollTimer = null } }
function startLogPolling(pipelineId: string) {
  stopLogPolling()
  logPollTimer = setInterval(async () => {
    try {
      const logs = (await automationApi.logs(pipelineId)).data.logs || []
      if (logs.length > 0) { pipelineLogs.value = logs; if (logs[0].status !== 'running') { stopLogPolling(); await loadPipelines() } }
    } catch { /* ignore */ }
  }, 2000)
}
watch(logPipeline, (v) => { if (!v) { stopLogPolling() } })
onUnmounted(stopLogPolling)

const editingPipeline = ref<Pipeline | null>(null)
const editForm = ref({ name: '', description: '', steps: [] as any[], trigger: 'manual', cron: '', ack: true })
const saving = ref(false)
const stepDragIdx = ref<number | null>(null)
const agentOptions = [
  { value: 'knowledge_gap', label: '🔍 知识缺口 Agent' },
  { value: 'literature', label: '📚 文献综述 Agent' },
  { value: 'hypothesis', label: '💡 假设生成 Agent' },
  { value: 'hypothesis_validator', label: '✅ 假设核验 Agent' },
  { value: 'design', label: '📐 研究设计 Agent' },
  { value: 'experiment_plan', label: '🧪 实验规划 Agent' },
  { value: 'analysis', label: '📊 数据分析 Agent' },
  { value: 'writing', label: '✍️ 论文撰写 Agent' },
  { value: 'review', label: '🔎 同行评审 Agent' },
  { value: 'reflection', label: '🔄 反思迭代 Agent' },
]
function openEditor(p: Pipeline) {
  editingPipeline.value = p
  editForm.value = { name: p.name, description: p.description || '', steps: JSON.parse(JSON.stringify(p.steps || [])), trigger: p.trigger || 'manual', cron: (p as any).schedule_cron || '', ack: true }
}
function onStepDrop(targetIdx: number) {
  if (stepDragIdx.value === null || stepDragIdx.value === targetIdx) return
  const s = editForm.value.steps.splice(stepDragIdx.value, 1)[0]
  editForm.value.steps.splice(targetIdx, 0, s); stepDragIdx.value = null
}
async function saveSteps() {
  if (!editingPipeline.value) return
  saving.value = true
  try {
    await automationApi.update(editingPipeline.value.id, {
      name: editForm.value.name, description: editForm.value.description,
      steps: editForm.value.steps.map(s => ({ agent_name: s.agent_name, name: s.agent_name, params: s.params || '', research_question: s.params || '' })),
      trigger: editForm.value.trigger,
      schedule_cron: editForm.value.cron || undefined,
    })
    appStore.showToast('✅ 流水线已更新', 'success'); editingPipeline.value = null; await loadPipelines()
  } catch (e: any) { appStore.showToast(e?.response?.data?.detail || '保存失败', 'error') }
  finally { saving.value = false }
}

onMounted(() => { loadPipelines(); loadTemplates() })
</script>