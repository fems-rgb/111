<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">🧪 实验模拟场</h1>
        <p class="text-sm text-gray-500 mt-1">代码驱动的科学实验模拟 · 图表生成 · 动态可视化</p>
      </div>
      <div class="flex gap-2">
        <button @click="openNewTemplate" class="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm hover:bg-emerald-700">➕ 新建模板</button>
        <button @click="showTemplates=true" class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700">📚 模板库</button>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <!-- 左侧：代码编辑 -->
      <div class="space-y-4">
        <div class="bg-white rounded-xl border overflow-hidden">
          <div class="px-4 py-3 border-b flex items-center justify-between">
            <span class="text-sm font-medium">📑 实验代码</span>
            <select v-model="selTplId" @change="onSelectTemplate" class="text-xs border rounded px-2 py-1">
              <option :value="null">选择模板...</option>
              <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
          </div>
          <textarea v-model="code" rows="18" spellcheck="false"
            class="w-full p-4 font-mono text-xs leading-relaxed resize-y focus:outline-none bg-gray-50"
            placeholder="# 在此编写实验代码...&#10;# 支持: numpy, matplotlib, scipy, pandas&#10;# plt.savefig() / plt.show() 自动捕获图表&#10;# 定义 result_data = {'columns':[], 'rows':[]} 输出数据表"></textarea>
        </div>
        <div class="flex items-center gap-4">
          <input v-model="expTitle" placeholder="实验名称" class="flex-1 px-3 py-2 border rounded-lg text-sm"/>
          <label class="flex items-center gap-1 text-sm whitespace-nowrap">
            <input type="checkbox" v-model="genVideo"/> 生成动画
          </label>
          <button @click="submitRun" :disabled="running || !code.trim()"
            class="px-6 py-2 rounded-lg font-medium text-white transition-all whitespace-nowrap"
            :class="running||!code.trim()?'bg-gray-300 cursor-not-allowed':'bg-emerald-600 hover:bg-emerald-700 shadow-lg'">
            {{ running ? '⏳ 运行中...' : '▶️ 运行实验' }}
          </button>
        </div>
      </div>

      <!-- 右侧：结果展示 -->
      <div class="space-y-4">
        <div v-if="result" class="bg-white rounded-xl border p-4 space-y-3">
          <div class="flex items-center gap-3">
            <span class="w-3 h-3 rounded-full"
              :class="{'bg-yellow-400 animate-pulse': result.status==='running', 'bg-green-500': result.status==='completed', 'bg-red-500': result.status==='failed'}">
            </span>
            <span class="text-sm font-medium">{{ statusLabel(result.status) }}</span>
            <span v-if="result.duration_ms" class="text-xs text-gray-400 ml-auto">⏱ {{ (result.duration_ms/1000).toFixed(1) }}秒</span>
          </div>

          <div v-if="result.error_message" class="bg-red-50 border border-red-200 rounded-lg p-3">
            <p class="text-xs font-medium text-red-600 mb-1">❌ 错误信息</p>
            <pre class="text-xs text-red-700 whitespace-pre-wrap">{{ result.error_message }}</pre>
          </div>

          <div v-if="result.output_text" class="bg-gray-900 rounded-lg p-3">
            <p class="text-xs text-gray-400 mb-1">🖥 控制台输出</p>
            <pre class="text-xs text-green-400 whitespace-pre-wrap max-h-40 overflow-y-auto">{{ result.output_text }}</pre>
          </div>

          <div v-if="result.data_table" class="overflow-x-auto border rounded-lg">
            <p class="text-xs text-gray-500 px-3 pt-2">📊 数据结果</p>
            <table class="w-full text-xs">
              <thead class="bg-gray-50"><tr>
                <th v-for="c in result.data_table.columns" :key="c" class="px-3 py-2 text-left border-b">{{ c }}</th>
              </tr></thead>
              <tbody><tr v-for="(row, i) in result.data_table.rows" :key="i" class="border-b last:border-0">
                <td v-for="(cell, j) in row" :key="j" class="px-3 py-1.5">{{ cell }}</td>
              </tr></tbody>
            </table>
          </div>

          <!-- 图表展示 -->
          <div v-if="result.charts && result.charts.length" class="space-y-3">
            <p class="text-xs text-gray-500"> 生成图表 ({{ result.charts.length }})</p>
            <div v-for="c in result.charts" :key="c.filename" class="relative group">
              <img :src="chartUrl(c)" :alt="c.filename"
                class="w-full rounded-lg border bg-gray-50" loading="lazy"
                @error="(e: any) => e.target.style.display='none'"
                @click="previewImage(chartUrl(c))"/>
              <p class="text-[10px] text-gray-400 mt-1 text-center">{{ c.filename }}</p>
            </div>
          </div>

          <!-- 视频展示 -->
          <div v-if="result.video_path">
            <p class="text-xs text-gray-500 mb-2">🎬 动态过程</p>
            <video v-if="isVideoFormat(result.video_path)" :src="videoUrl()" controls autoplay loop
              class="w-full rounded-lg border bg-black" preload="metadata"></video>
            <img v-else :src="videoUrl()" class="w-full rounded-lg border" loading="lazy"
              @click="previewImage(videoUrl())"/>
          </div>
        </div>

        <div v-else class="bg-white rounded-xl border-dashed border-2 p-12 text-center">
          <p class="text-4xl mb-3">🔬</p>
          <p class="text-gray-500">编写代码并点击「运行实验」查看结果</p>
          <p class="text-xs text-gray-400 mt-2">支持 numpy · matplotlib · scipy · pandas</p>
        </div>
      </div>
    </div>

    <!-- ========== 历史记录区域 ========== -->
    <div class="bg-white rounded-xl border overflow-hidden">
      <div class="px-4 py-3 border-b flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="text-sm font-medium">📋 历史记录</span>
          <span class="text-xs text-gray-400">共 {{ historyTotal }} 条</span>
        </div>
        <div class="flex items-center gap-2">
          <button v-if="selectedIds.size > 0" @click="batchDelete"
            class="px-3 py-1.5 rounded-lg bg-red-500 text-white text-xs hover:bg-red-600 transition-colors">
            🗑 批量删除 ({{ selectedIds.size }})
          </button>
          <button @click="loadHistory" class="px-3 py-1.5 rounded-lg border text-xs text-gray-500 hover:bg-gray-50">
            🔄 刷新
          </button>
        </div>
      </div>

      <div v-if="historyItems.length === 0" class="p-8 text-center text-gray-400 text-sm">
        暂无历史记录
      </div>

      <div v-else class="divide-y">
        <div v-for="item in historyItems" :key="item.run_id"
          class="px-4 py-3 flex items-center gap-3 hover:bg-gray-50 transition-colors group"
          :class="{'bg-blue-50/50': selectedIds.has(item.run_id)}">
          <!-- 多选框 -->
          <input type="checkbox" :checked="selectedIds.has(item.run_id)"
            @change="toggleSelect(item.run_id)"
            class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer flex-shrink-0"/>

          <!-- 状态指示 -->
          <span class="w-2.5 h-2.5 rounded-full flex-shrink-0"
            :class="{'bg-green-500': item.status==='completed', 'bg-red-500': item.status==='failed', 'bg-yellow-400 animate-pulse': item.status==='running', 'bg-gray-300': item.status==='pending'}">
          </span>

          <!-- 信息 -->
          <div class="flex-1 min-w-0 cursor-pointer" @click="viewHistoryItem(item.run_id)">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium truncate">{{ item.title || '未命名实验' }}</span>
              <span v-if="item.charts_count > 0" class="text-[10px] px-1.5 py-0.5 bg-emerald-50 text-emerald-600 rounded">
                📈 {{ item.charts_count }}图
              </span>
              <span v-if="item.has_video" class="text-[10px] px-1.5 py-0.5 bg-purple-50 text-purple-600 rounded">
                🎬 视频
              </span>
            </div>
            <div class="flex items-center gap-3 mt-0.5">
              <span class="text-[11px] text-gray-400">{{ formatTime(item.created_at) }}</span>
              <span v-if="item.duration_ms" class="text-[11px] text-gray-400">⏱ {{ (item.duration_ms/1000).toFixed(1) }}s</span>
              <span class="text-[11px]" :class="item.status==='completed'?'text-green-500':item.status==='failed'?'text-red-500':'text-yellow-500'">
                {{ statusLabel(item.status) }}
              </span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button @click.stop="viewHistoryItem(item.run_id)"
              class="p-1.5 rounded-lg hover:bg-blue-100 text-blue-500 text-xs" title="查看详情">👁</button>
            <button @click.stop="deleteSingle(item.run_id)"
              class="p-1.5 rounded-lg hover:bg-red-100 text-red-400 text-xs" title="删除">🗑</button>
          </div>
        </div>
      </div>

      <!-- 分页 + 全选 -->
      <div v-if="historyTotal > 0" class="px-4 py-2.5 border-t flex items-center justify-between bg-gray-50/50">
        <label class="flex items-center gap-2 text-xs text-gray-500 cursor-pointer">
          <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll"
            class="w-3.5 h-3.5 rounded border-gray-300 text-blue-600"/>
          全选当前页
        </label>
        <div class="flex items-center gap-2">
          <button @click="historyPage > 1 && (historyPage--, loadHistory())"
            :disabled="historyPage <= 1"
            class="px-2 py-1 text-xs rounded border" :class="historyPage<=1?'text-gray-300':'text-gray-600 hover:bg-gray-100'">
            ◀ 上一页
          </button>
          <span class="text-xs text-gray-500">{{ historyPage }} / {{ Math.max(1, Math.ceil(historyTotal / historyPageSize)) }}</span>
          <button @click="historyPage < Math.ceil(historyTotal/historyPageSize) && (historyPage++, loadHistory())"
            :disabled="historyPage >= Math.ceil(historyTotal/historyPageSize)"
            class="px-2 py-1 text-xs rounded border" :class="historyPage>=Math.ceil(historyTotal/historyPageSize)?'text-gray-300':'text-gray-600 hover:bg-gray-100'">
            下一页 ▶
          </button>
        </div>
      </div>
    </div>

    <!-- 图片预览弹窗 -->
    <div v-if="previewUrl" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-8" @click="previewUrl=null">
      <img :src="previewUrl" class="max-w-full max-h-full rounded-lg shadow-2xl" @click.stop/>
      <button @click="previewUrl=null" class="absolute top-4 right-4 text-white text-2xl hover:text-gray-300">✕</button>
    </div>

    <!-- 模板库弹窗 -->
    <div v-if="showTemplates" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showTemplates=false">
      <div class="bg-white rounded-2xl p-6 w-full max-w-lg shadow-2xl max-h-[80vh] overflow-y-auto">
        <h3 class="text-lg font-bold mb-4">📚 实验模板库</h3>
        <div v-if="templates.length === 0" class="text-center text-gray-400 py-8">暂无模板，点击「新建模板」创建</div>
        <div class="space-y-3">
          <div v-for="t in templates" :key="t.id"
            class="p-4 border rounded-xl hover:border-blue-400 hover:bg-blue-50 transition-all group">
            <div class="flex items-start justify-between">
              <div class="flex-1 cursor-pointer" @click="applyTemplate(t.id)">
                <div class="flex items-center gap-2">
                  <p class="font-medium text-sm">{{ t.name }}</p>
                  <span v-if="t.is_builtin" class="text-[10px] px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded">内置</span>
                  <span class="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">{{ t.category }}</span>
                </div>
                <p class="text-xs text-gray-500 mt-1">{{ t.description }}</p>
              </div>
              <button v-if="!t.is_builtin" @click.stop="removeTemplate(t.id)"
                class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 text-xs ml-2 transition-opacity">删除</button>
            </div>
          </div>
        </div>
        <button @click="showTemplates=false" class="mt-4 w-full py-2 text-sm text-gray-500 hover:text-gray-700">关闭</button>
      </div>
    </div>

    <!-- 新建模板弹窗 -->
    <div v-if="showNewTpl" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showNewTpl=false">
      <div class="bg-white rounded-2xl p-6 w-full max-w-2xl shadow-2xl">
        <h3 class="text-lg font-bold mb-4">➕ 新建实验模板</h3>
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <input v-model="newTpl.name" placeholder="模板名称" class="px-3 py-2 border rounded-lg text-sm"/>
            <input v-model="newTpl.category" placeholder="分类（如：统计分析）" class="px-3 py-2 border rounded-lg text-sm"/>
          </div>
          <input v-model="newTpl.description" placeholder="模板描述" class="w-full px-3 py-2 border rounded-lg text-sm"/>
          <textarea v-model="newTpl.code" rows="12" spellcheck="false"
            class="w-full p-3 font-mono text-xs border rounded-lg bg-gray-50 resize-y"
            placeholder="# 在此编写模板代码..."></textarea>
        </div>
        <div class="flex gap-3 mt-4">
          <button @click="saveNewTemplate" :disabled="!newTpl.name||!newTpl.code.trim()"
            class="flex-1 py-2 rounded-lg text-white text-sm font-medium"
            :class="!newTpl.name||!newTpl.code.trim()?'bg-gray-300':'bg-emerald-600 hover:bg-emerald-700'">保存模板</button>
          <button @click="showNewTpl=false" class="px-6 py-2 rounded-lg border text-sm text-gray-500 hover:bg-gray-50">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  runExperiment, getExperimentStatus, getExperimentTemplates,
  getTemplateCode, createTemplate, deleteTemplate,
  getChartUrl, getVideoUrl, isVideoFormat,
  getExperimentHistory, deleteExperimentRun, batchDeleteExperimentRuns,
  type ExperimentStatus, type TemplateInfo
} from '@/api/modules/experiment'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const code = ref('')
const expTitle = ref('')
const genVideo = ref(true)
const running = ref(false)
const result = ref<ExperimentStatus | null>(null)
const templates = ref<TemplateInfo[]>([])
const selTplId = ref<number | null>(null)
const showTemplates = ref(false)
const showNewTpl = ref(false)
const newTpl = ref({ name: '', description: '', code: '', category: '自定义' })
const previewUrl = ref<string | null>(null)
let timer: any = null

// ===== 历史记录 =====
const historyItems = ref<any[]>([])
const historyTotal = ref(0)
const historyPage = ref(1)
const historyPageSize = 10
const selectedIds = ref<Set<number>>(new Set())

const isAllSelected = computed(() =>
  historyItems.value.length > 0 && historyItems.value.every((i: any) => selectedIds.value.has(i.run_id))
)

function toggleSelect(id: number) {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  selectedIds.value = s
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(historyItems.value.map((i: any) => i.run_id))
  }
}

async function loadHistory() {
  try {
    const r = await getExperimentHistory({ page: historyPage.value, page_size: historyPageSize })
    historyItems.value = r.data.items
    historyTotal.value = r.data.total
  } catch { /* silent */ }
}

async function viewHistoryItem(runId: number) {
  try {
    const r = await getExperimentStatus(runId)
    result.value = r.data
    // 回填代码和标题
    if (r.data.title) expTitle.value = r.data.title
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e: any) {
    store.showToast('加载详情失败', 'error')
  }
}

async function deleteSingle(runId: number) {
  if (!confirm('确定删除此实验记录？')) return
  try {
    await deleteExperimentRun(runId)
    store.showToast('🗑️ 已删除', 'success')
    selectedIds.value.delete(runId)
    selectedIds.value = new Set(selectedIds.value)
    await loadHistory()
  } catch (e: any) {
    store.showToast('删除失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

async function batchDelete() {
  const ids = Array.from(selectedIds.value)
  if (ids.length === 0) return
  if (!confirm(`确定删除选中的 ${ids.length} 条实验记录？此操作不可恢复。`)) return
  try {
    const r = await batchDeleteExperimentRuns(ids)
    store.showToast(`🗑️ ${r.data.message}`, 'success')
    selectedIds.value = new Set()
    await loadHistory()
  } catch (e: any) {
    store.showToast('批量删除失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

function previewImage(url: string) {
  previewUrl.value = url
}

function formatTime(iso: string | null) {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch { return iso }
}

// ===== 实验运行 =====
async function submitRun() {
  if (!code.value.trim() || running.value) return
  running.value = true
  result.value = null
  try {
    const r = await runExperiment({
      code: code.value,
      title: expTitle.value || '未命名实验',
      generate_video: genVideo.value,
      timeout: 120
    })
    poll(r.data.run_id)
    store.showToast('🧪 实验已提交运行', 'success')
  } catch (e: any) {
    store.showToast('提交失败: ' + (e.response?.data?.detail || e.message), 'error')
    running.value = false
  }
}

function poll(id: number) {
  if (timer) clearInterval(timer)
  timer = setInterval(async () => {
    try {
      const r = await getExperimentStatus(id)
      result.value = r.data
      if (r.data.status === 'completed' || r.data.status === 'failed') {
        clearInterval(timer); timer = null; running.value = false
        if (r.data.status === 'completed') {
          store.showToast('✅ 实验完成！', 'success')
          await loadHistory()  // 刷新历史
        } else {
          store.showToast('❌ 实验失败', 'error')
          await loadHistory()
        }
      }
    } catch { /* ignore polling errors */ }
  }, 2000)
}

function chartUrl(c: { filename: string }) {
  return result.value ? getChartUrl(result.value.run_id, c.filename) : ''
}
function videoUrl() {
  return result.value ? getVideoUrl(result.value.run_id) : ''
}
function statusLabel(s: string) {
  return ({ pending: '等待中', running: '运行中', completed: '已完成', failed: '失败' } as any)[s] || s
}

// ===== 模板管理 =====
async function loadTemplates() {
  try {
    const r = await getExperimentTemplates()
    templates.value = r.data.templates
  } catch { /* silent */ }
}

async function applyTemplate(id: number) {
  try {
    const r = await getTemplateCode(id)
    code.value = r.data.code
    expTitle.value = r.data.name
    selTplId.value = id
    showTemplates.value = false
    store.showToast('📋 已加载模板: ' + r.data.name, 'success')
  } catch (e: any) {
    store.showToast('加载模板失败', 'error')
  }
}

function onSelectTemplate() {
  if (selTplId.value) applyTemplate(selTplId.value)
}

function openNewTemplate() {
  if (code.value.trim()) {
    newTpl.value.code = code.value
    newTpl.value.name = expTitle.value || ''
  } else {
    newTpl.value = { name: '', description: '', code: '', category: '自定义' }
  }
  showNewTpl.value = true
}

async function saveNewTemplate() {
  if (!newTpl.value.name || !newTpl.value.code.trim()) return
  try {
    await createTemplate(newTpl.value)
    store.showToast('✅ 模板已保存', 'success')
    showNewTpl.value = false
    await loadTemplates()
  } catch (e: any) {
    store.showToast('保存失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

async function removeTemplate(id: number) {
  if (!confirm('确定删除此模板？')) return
  try {
    await deleteTemplate(id)
    store.showToast('🗑️ 模板已删除', 'success')
    await loadTemplates()
  } catch (e: any) {
    store.showToast('删除失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

onMounted(() => {
  loadTemplates()
  loadHistory()
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>
