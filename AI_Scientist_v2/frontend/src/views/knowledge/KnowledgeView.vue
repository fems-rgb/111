<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Tab切换 -->
    <div class="flex gap-1 bg-surface-100 p-1 rounded-lg w-fit mb-4">
      <button @click="activeTab = 'local'" :class="['px-4 py-2 rounded-md text-sm font-medium transition-all', activeTab === 'local' ? 'bg-white shadow text-primary-700' : 'text-surface-500 hover:text-surface-700']">
        📂 本地资料库
      </button>
      <button @click="activeTab = 'external'" :class="['px-4 py-2 rounded-md text-sm font-medium transition-all', activeTab === 'external' ? 'bg-white shadow text-primary-700' : 'text-surface-500 hover:text-surface-700']">
        🌐 外部资料搜索
      </button>
      <button @click="activeTab = 'url'" :class="['px-4 py-2 rounded-md text-sm font-medium transition-all', activeTab === 'url' ? 'bg-white shadow text-primary-700' : 'text-surface-500 hover:text-surface-700']">
        🔗 URL抓取
      </button>
    </div>

    <!-- ===== 外部资料搜索面板 ===== -->
    <div v-if="activeTab === 'external'" class="space-y-4 animate-fade-in">
      <div class="card border-l-4 border-l-indigo-500">
        <h2 class="text-lg font-semibold mb-3 flex items-center gap-2">
          🔬 AI自主搜寻学术资料
          <span class="text-xs font-normal text-surface-400">Semantic Scholar + arXiv + OpenAlex + Crossref + Europe PMC 多源并发搜索</span>
        </h2>
        <div class="flex gap-3 items-end">
          <div class="flex-1">
            <label class="block text-xs font-medium text-surface-600 mb-1">搜索关键词</label>
            <input v-model="extSearchQuery" @keydown.enter="doExternalSearch" class="input-field" placeholder="例如：transformer attention mechanism / 大语言模型对齐..." />
          </div>
          <div class="w-32">
            <label class="block text-xs font-medium text-surface-600 mb-1">数据源</label>
            <select v-model="extSources" class="input-field text-sm">
              <option value="semantic_scholar,arxiv,openalex,crossref,europepmc">全部</option>
              <option value="semantic_scholar">Semantic Scholar</option>
              <option value="arxiv">arXiv</option>
              <option value="openalex">OpenAlex</option>
              <option value="crossref">Crossref</option>
              <option value="europepmc">Europe PMC</option>
            </select>
          </div>
          <div class="w-24">
            <label class="block text-xs font-medium text-surface-600 mb-1">数量</label>
            <select v-model="extLimit" class="input-field text-sm">
              <option :value="5">5条</option>
              <option :value="10">10条</option>
              <option :value="20">20条</option>
            </select>
          </div>
          <button @click="doExternalSearch" :disabled="extSearching" class="btn-primary whitespace-nowrap">
            {{ extSearching ? '⏳ 搜索中...' : '🔍 搜索' }}
          </button>
        </div>
      </div>

      <!-- 搜索结果 -->
      <div v-if="extResults.length > 0" class="space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-sm text-surface-500">找到 {{ extTotalFound }} 条结果（{{ extSourceCounts }}）</span>
          <button @click="batchImportSelected" :disabled="extImporting || selectedExtIds.length === 0" class="btn-primary text-sm">
            {{ extImporting ? '⏳ 导入中...' : '📥 批量导入选中' }}
          </button>
        </div>
        <!-- 多线程导入进度 -->
        <div v-if="extImporting" class="card p-3">
          <div class="flex items-center gap-3">
            <span class="inline-block w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></span>
            <span class="text-sm">多线程导入中... ({{ extImportProgress.current }}/{{ extImportProgress.total }})</span>
            <div class="flex-1 h-2 bg-surface-100 rounded-full overflow-hidden">
              <div class="h-full bg-indigo-500 transition-all duration-300 rounded-full"
                   :style="{ width: (extImportProgress.total ? (extImportProgress.current / extImportProgress.total * 100) : 0) + '%' }"></div>
            </div>
          </div>
        </div>
        <!-- 论文卡片列表 -->
        <div v-for="(paper, idx) in extResults" :key="idx"
             class="card p-4 hover:ring-2 ring-indigo-200 transition-all cursor-pointer"
             @click="toggleExtSelect(idx)">
          <div class="flex items-start gap-3">
            <input type="checkbox" :checked="selectedExtIds.includes(idx)" @click.stop="toggleExtSelect(idx)" class="mt-1 rounded" />
            <div class="flex-1 min-w-0">
              <h3 class="font-semibold text-sm line-clamp-1">{{ paper.title }}</h3>
              <p class="text-xs text-surface-500 mt-1">
                {{ paper.authors?.slice(0,3).join(', ') }}{{ paper.authors?.length > 3 ? ' et al.' : '' }}
                · {{ paper.year || '?' }} · 📊 {{ paper.citations || 0 }} citations
                · <span class="text-indigo-600">{{ paper.source }}</span>
              </p>
              <p class="text-xs text-surface-400 mt-1 line-clamp-2">{{ paper.abstract }}</p>
              <div class="flex gap-2 mt-2">
                <a v-if="paper.url" :href="paper.url" target="_blank" @click.stop class="text-xs text-primary-600 hover:underline">📄 原文</a>
                <a v-if="paper.pdf_url" :href="paper.pdf_url" target="_blank" @click.stop class="text-xs text-green-600 hover:underline">📥 PDF</a>
                <button @click.stop="quickImportOne(paper)" :disabled="quickImportingId === paper.id" class="text-xs font-medium" :class="quickImportingId === paper.id ? 'text-gray-400 cursor-not-allowed' : 'text-indigo-600 hover:underline'">{{ quickImportingId === paper.id ? '⏳ 导入中...' : '⚡ 快速导入' }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else-if="extSearched && !extSearching" class="text-center py-12 text-surface-400">
        未找到相关论文，请尝试其他关键词
      </div>
    </div>

    <!-- ===== URL抓取面板 ===== -->
    <div v-if="activeTab === 'url'" class="space-y-4 animate-fade-in">
      <div class="card border-l-4 border-l-green-500">
        <h2 class="text-lg font-semibold mb-3 flex items-center gap-2">
          🔗 外部URL资料抓取
          <span class="text-xs font-normal text-surface-400">支持PDF直链、网页文章提取，多线程并发</span>
        </h2>
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-surface-600 mb-1">URL列表（每行一个，最多10个）</label>
            <textarea v-model="urlInput" class="input-field h-28 resize-none font-mono text-sm"
              placeholder="https://arxiv.org/pdf/2301.00001.pdf&#10;https://example.com/research-paper&#10;https://doi.org/10.1234/example"></textarea>
          </div>
          <button @click="doBatchFetch" :disabled="urlFetching" class="btn-primary">
            {{ urlFetching ? '⏳ 多线程抓取中...' : '🚀 并发抓取并导入' }}
          </button>
        </div>
      </div>
      <div v-if="urlFetchResults.length > 0" class="space-y-2">
        <h3 class="text-sm font-semibold">抓取结果</h3>
        <div v-for="(r, i) in urlFetchResults" :key="i" class="card p-3 text-sm">
          <div class="flex items-center gap-2">
            <span :class="r.error ? 'text-red-500' : 'text-green-500'">{{ r.error ? '❌' : '✅' }}</span>
            <span class="truncate flex-1">{{ r.url }}</span>
            <span class="text-xs text-surface-400">{{ r.type || '' }}</span>
          </div>
          <p v-if="r.error" class="text-xs text-red-400 mt-1">{{ r.error }}</p>
        </div>
      </div>
    </div>

    <!-- ===== 本地资料库（原有内容） ===== -->
    <div v-show="activeTab === 'local'">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-surface-800">📚 知识库</h1>
      <div class="flex gap-3">
        <input v-model="searchQuery" type="text" placeholder="搜索文档..." class="input-field w-64 text-sm" @input="debouncedSearch" />
        <button class="btn-secondary text-sm px-4 py-2 rounded-lg border border-surface-300 hover:bg-surface-100 transition-colors" :disabled="reindexingAll" @click="handleReindexAll">
          <span v-if="reindexingAll" class="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin mr-1"></span>
          {{ reindexingAll ? '重建中...' : '🔄 全量重建索引' }}
        </button>
        <button v-if="selectedIds.length > 0" class="btn-danger text-sm px-4 py-2" @click="handleBatchDelete">
          🗑️ 批量删除 ({{ selectedIds.length }})
        </button>
        <label class="btn-primary text-sm cursor-pointer flex items-center gap-1 px-4 py-2">
          + 上传文献
          <input type="file" class="hidden" multiple :accept="ACCEPT_STRING" @change="handleUpload" />
        </label>
      </div>
    </div>

    <!-- 拖拽上传区域 -->
    <div
      class="border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="handleDrop"
      :class="isDragging
        ? 'border-primary-500 bg-primary-50 scale-[1.01] shadow-lg ring-2 ring-primary-200'
        : 'border-surface-300 hover:border-primary-400 hover:bg-primary-50/30'"
    >
      <span class="text-3xl block mb-2">{{ isDragging ? '🎯' : '📂' }}</span>
      <p class="text-sm text-surface-600 font-medium">{{ isDragging ? '松开鼠标即可上传！' : '拖拽文件到此处上传，或点击上方按钮选择' }}</p>
      <p class="text-xs mt-1 text-surface-400">支持 PDF / Word / Excel / PPT / Markdown / CSV / TXT / Python / JSON / 图片，单文件最大 50MB</p>
    </div>

    <div class="grid grid-cols-4 gap-4">
      <div class="card p-4">
        <div class="text-sm text-surface-500">总文档数</div>
        <div class="text-2xl font-bold text-surface-800">{{ stats.total_docs ?? 0 }}</div>
      </div>
      <div class="card p-4">
        <div class="text-sm text-surface-500">已索引</div>
        <div class="text-2xl font-bold text-green-600">{{ stats.indexed ?? 0 }}</div>
      </div>
      <div class="card p-4">
        <div class="text-sm text-surface-500">处理中</div>
        <div class="text-2xl font-bold text-yellow-600">{{ stats.processing ?? 0 }}</div>
      </div>
      <div class="card p-4">
        <div class="text-sm text-surface-500">总大小</div>
        <div class="text-2xl font-bold text-surface-800">{{ formatSize(stats.total_size) }}</div>
      </div>
    </div>

    <div v-if="uploading" class="card p-4">
      <div class="flex items-center gap-3">
        <span class="inline-block w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></span>
        <span class="text-sm text-surface-600">正在上传并索引文档... ({{ uploadProgress.current }}/{{ uploadProgress.total }})</span>
        <div class="flex-1 h-2 bg-surface-100 rounded-full overflow-hidden ml-3">
          <div class="h-full bg-primary-500 transition-all duration-300 rounded-full"
               :style="{ width: (uploadProgress.total ? (uploadProgress.current / uploadProgress.total * 100) : 0) + '%' }"></div>
        </div>
      </div>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-surface-50 border-b border-surface-200">
          <tr>
            <th class="text-left p-3 w-10">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" class="rounded border-surface-300" />
            </th>
            <th class="text-left p-3 font-medium text-surface-600">文档名称</th>
            <th class="text-left p-3 font-medium text-surface-600">类型</th>
            <th class="text-left p-3 font-medium text-surface-600">大小</th>
            <th class="text-left p-3 font-medium text-surface-600">状态</th>
            <th class="text-left p-3 font-medium text-surface-600">上传时间</th>
            <th class="text-right p-3 font-medium text-surface-600">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-if="loading">
            <td colspan="7" class="p-8 text-center text-surface-400">加载中...</td>
          </tr>
          <tr v-else-if="docs.length === 0">
            <td colspan="7" class="p-8 text-center text-surface-400">
              <span class="text-3xl block mb-2">📄</span>
              <p>暂无文档，拖拽或点击上传开始</p>
            </td>
          </tr>
          <tr v-for="doc in docs" :key="doc.id"
              :class="['hover:bg-surface-50 transition-colors', selectedIds.includes(doc.id) ? 'bg-primary-50/50' : '']">
            <td class="p-3">
              <input type="checkbox" :checked="selectedIds.includes(doc.id)"
                     @change="toggleSelect(doc.id)" class="rounded border-surface-300" />
            </td>
            <td class="p-3 font-medium text-surface-800">
              <button class="hover:text-primary-600 hover:underline" @click="previewDoc(doc)">{{ doc.title }}</button>
            </td>
            <td class="p-3"><span class="px-2 py-0.5 bg-surface-100 rounded text-xs font-mono">{{ doc.doc_type }}</span></td>
            <td class="p-3 text-surface-500">{{ formatSize(doc.file_size) }}</td>
            <td class="p-3">
              <span :class="getStatusClass(doc.status)" class="px-2 py-0.5 rounded text-xs font-medium">{{ getStatusLabel(doc.status) }}</span>
            </td>
            <td class="p-3 text-surface-500">{{ formatDate(doc.created_at) }}</td>
            <td class="p-3 text-right space-x-2">
              <button class="text-xs text-primary-500 hover:underline" @click="previewDoc(doc)">预览</button>
              <button class="text-xs text-red-500 hover:underline" @click="deleteDoc(doc.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 文档预览弹窗 -->
    <Teleport to="body">
      <div v-if="previewVisible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="previewVisible = false">
        <div class="bg-white rounded-2xl shadow-2xl w-[90vw] h-[85vh] flex flex-col overflow-hidden">
          <div class="flex items-center justify-between px-6 py-4 border-b border-surface-200">
            <h3 class="font-semibold text-surface-800 truncate">{{ previewTitle }}</h3>
            <button class="text-surface-400 hover:text-surface-700 text-xl" @click="previewVisible = false">&times;</button>
          </div>
          <div class="flex-1 overflow-auto p-6">
            <!-- ✅ 图片预览 -->
            <div v-if="previewIsImage" class="flex items-center justify-center h-full">
              <img :src="previewImageUrl" class="max-w-full max-h-full object-contain rounded-lg shadow-lg" />
            </div>
            <!-- ✅ PDF 预览 -->
            <iframe v-else-if="previewIsPdf" :src="previewPdfUrl" class="w-full h-full border-0 rounded-lg"></iframe>
            <!-- ✅ Meta文献预览 -->
            <div v-else-if="previewIsMeta && previewMetaData" class="space-y-5">
              <!-- 顶部操作栏 -->
              <div class="flex items-center gap-3 flex-wrap">
                <a v-if="previewMetaData.url" :href="previewMetaData.url" target="_blank" rel="noopener"
                   class="inline-flex items-center gap-1.5 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition text-sm font-medium shadow-sm">
                  🔗 阅读原文
                </a>
                <span v-if="previewMetaData.source" class="px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-medium">{{ previewMetaData.source }}</span>
                <span v-if="previewMetaData.year" class="px-2.5 py-1 bg-surface-100 text-surface-600 rounded-full text-xs">{{ previewMetaData.year }}年</span>
                <span v-if="previewMetaData.citations" class="px-2.5 py-1 bg-amber-50 text-amber-700 rounded-full text-xs">📊 引用 {{ previewMetaData.citations }}</span>
              </div>
              <!-- 摘要 -->
              <div v-if="previewMetaData.summary || previewMetaData.abstract" class="bg-surface-50 rounded-xl p-5 border border-surface-200">
                <h4 class="text-sm font-semibold text-surface-500 mb-2 flex items-center gap-1.5">📝 摘要</h4>
                <p class="text-sm text-surface-700 leading-relaxed whitespace-pre-wrap">{{ previewMetaData.abstract || previewMetaData.summary }}</p>
              </div>
              <!-- 元信息卡片 -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div v-if="previewMetaData.authors?.length" class="bg-white rounded-lg border border-surface-200 p-3 col-span-2">
                  <div class="text-xs text-surface-400 mb-1">👤 作者</div>
                  <div class="text-sm text-surface-700">{{ Array.isArray(previewMetaData.authors) ? previewMetaData.authors.join(", ") : previewMetaData.authors }}</div>
                </div>
                <div v-if="previewMetaData.doi" class="bg-white rounded-lg border border-surface-200 p-3">
                  <div class="text-xs text-surface-400 mb-1">🔖 DOI</div>
                  <div class="text-sm text-surface-700 break-all">{{ previewMetaData.doi }}</div>
                </div>
                <div v-if="previewMetaData.source" class="bg-white rounded-lg border border-surface-200 p-3">
                  <div class="text-xs text-surface-400 mb-1">📚 来源</div>
                  <div class="text-sm text-surface-700 capitalize">{{ previewMetaData.source }}</div>
                </div>
              </div>
              <!-- 无URL时的提示 -->
              <div v-if="!previewMetaData.url" class="text-center py-4 text-surface-400 text-sm">
                ⚠️ 该文献暂无可跳转的原文链接
              </div>
            </div>
            <!-- 文本预览 -->
            <pre v-else-if="previewContent" class="whitespace-pre-wrap text-sm text-surface-700 dark:text-surface-200 font-mono leading-relaxed">{{ previewContent }}</pre>
            <div v-else class="flex items-center justify-center h-full text-surface-400">
              <span v-if="previewLoading" class="inline-block w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mr-2"></span>
              {{ previewLoading ? '加载中...' : '该文档类型暂不支持预览' }}
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { ExternalPaper } from '@/api/modules/knowledge'
import { knowledgeApi, type KnowledgeDoc } from '@/api/modules/knowledge'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

// ===== Tab切换 =====
const activeTab = ref<'local' | 'external' | 'url'>('local')

// ===== 外部搜索状态 =====
const extSearchQuery = ref('')
const extSources = ref('semantic_scholar,arxiv,openalex,crossref,europepmc')
const extLimit = ref(10)
const extSearching = ref(false)
const extSearched = ref(false)
const extResults = ref<ExternalPaper[]>([])
const extTotalFound = ref(0)
const extSourceCounts = ref('')
const selectedExtIds = ref<number[]>([])
const extImporting = ref(false)
const extImportProgress = ref({ current: 0, total: 0 })
const quickImportingId = ref<string | null>(null)

// ===== URL抓取状态 =====
const urlInput = ref('')
const urlFetching = ref(false)
const urlFetchResults = ref<any[]>([])

async function doExternalSearch() {
  if (!extSearchQuery.value.trim()) return
  extSearching.value = true
  extSearched.value = false
  selectedExtIds.value = []
  try {
    const res = await knowledgeApi.searchExternal({
      q: extSearchQuery.value,
      sources: extSources.value,
      limit: extLimit.value,
    })
    const data = res.data
    extResults.value = data.papers || []
    extTotalFound.value = data.total || 0
    const sc = data.source_counts || {}
    extSourceCounts.value = Object.entries(sc).map(([k,v]) => `${k}: ${v}`).join(', ')
    if(data.hint) appStore.showToast(data.hint, 'info')
  } catch (e: any) {
    appStore.showToast('搜索失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    extSearching.value = false
    extSearched.value = true
  }
}

function toggleExtSelect(idx: number) {
  const pos = selectedExtIds.value.indexOf(idx)
  if (pos >= 0) selectedExtIds.value.splice(pos, 1)
  else selectedExtIds.value.push(idx)
}

async function quickImportOne(paper: ExternalPaper) {
  if (quickImportingId.value === paper.id) return
  quickImportingId.value = paper.id
  try {
    const res = await knowledgeApi.importPaper(paper)
    appStore.showToast('✅ 已导入: ' + (res.data?.filename || paper.title.slice(0, 30)), 'success')
    loadStats()
  } catch (e: any) {
    appStore.showToast('导入失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    quickImportingId.value = null
  }
}

async function batchImportSelected() {
  if (selectedExtIds.value.length === 0) return
  const papers = selectedExtIds.value.map(i => extResults.value[i]).filter(Boolean)
  extImporting.value = true
  extImportProgress.value = { current: 0, total: papers.length }
  let imported = 0
  let failed = 0
  for (const paper of papers) {
    try {
      await knowledgeApi.importPaper(paper)
      imported++
    } catch {
      failed++
    }
    extImportProgress.value.current++
  }
  if (imported > 0) {
    appStore.showToast(`✅ 成功导入 ${imported} 篇` + (failed > 0 ? `，${failed} 篇失败` : ''), 'success')
    selectedExtIds.value = []
    loadStats()
  } else {
    appStore.showToast('批量导入全部失败', 'error')
  }
  extImporting.value = false
  extImportProgress.value = { current: 0, total: 0 }
}

async function doBatchFetch() {
  const urls = urlInput.value.split('\n').map(u => u.trim()).filter(u => u && u.startsWith('http'))
  if (urls.length === 0) {
    appStore.showToast('请输入有效的URL', 'error')
    return
  }
  urlFetching.value = true
  urlFetchResults.value = []
  try {
    const res = await knowledgeApi.fetchUrlsBatch(urls)
    urlFetchResults.value = res.data.results || []
    const ok = urlFetchResults.value.filter((r: any) => !r.error).length
    appStore.showToast(`✅ 抓取完成: ${urlFetchResults.value.length} 条，成功 ${ok}`, ok > 0 ? 'success' : 'error')
  } catch (e: any) {
    appStore.showToast('抓取失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    urlFetching.value = false
  }
}
const docs = ref<KnowledgeDoc[]>([])
const stats = ref<any>({ total_docs: 0, indexed: 0, processing: 0, total_size: 0 })
const loading = ref(false)
const uploading = ref(false)
const searchQuery = ref('')
const isDragging = ref(false)
const reindexingAll = ref(false)
let searchTimer: ReturnType<typeof setTimeout> | null = null

// 多选
const selectedIds = ref<number[]>([])
const isAllSelected = computed(() => docs.value.length > 0 && selectedIds.value.length === docs.value.length)

function toggleSelect(id: number) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function toggleSelectAll() {
  if (isAllSelected.value) selectedIds.value = []
  else selectedIds.value = docs.value.map(d => d.id)
}

async function handleBatchDelete() {
  if (!confirm(`确定批量删除 ${selectedIds.value.length} 个文档？此操作不可恢复。`)) return
  let success = 0
  for (const id of selectedIds.value) {
    try { await knowledgeApi.deleteDoc(id); success++ } catch {}
  }
  appStore.showToast(`✅ 已删除 ${success}/${selectedIds.value.length} 个文档`, success > 0 ? 'success' : 'error')
  selectedIds.value = []
  await Promise.all([loadDocs(), loadStats()])
}

// Preview state
const previewVisible = ref(false)
const previewTitle = ref('')
const previewContent = ref('')
const previewLoading = ref(false)
const previewIsImage = ref(false)
const previewIsPdf = ref(false)
const previewImageUrl = ref('')
const previewPdfUrl = ref('')
const previewIsMeta = ref(false)
const previewMetaData = ref<any>(null)

const MAX_FILE_SIZE = 50 * 1024 * 1024
// ✅ 扩展支持的文件类型
const ALLOWED_EXTS = /\.(pdf|md|csv|txt|py|json|xlsx|xls|docx|doc|pptx|png|jpg|jpeg|gif|webp)$/i
const ACCEPT_STRING = '.pdf,.md,.csv,.txt,.py,.json,.xlsx,.xls,.docx,.doc,.pptx,.png,.jpg,.jpeg,.gif,.webp'

const uploadProgress = ref({ current: 0, total: 0 })

const loadDocs = async () => {
  loading.value = true
  try {
    const res = await knowledgeApi.listDocs({ search: searchQuery.value || undefined, limit: 100 })
    docs.value = res.data as any
  } catch (e) {
    console.error('Failed to load documents', e)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await knowledgeApi.getStats()
    stats.value = res.data
  } catch {}
}

const debouncedSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(loadDocs, 300)
}

const validateFiles = (files: File[]): File[] => {
  const valid: File[] = []
  for (const f of files) {
    if (f.size > MAX_FILE_SIZE) {
      appStore.showToast(f.name + ' 超过50MB限制', 'error')
      continue
    }
    if (!ALLOWED_EXTS.test(f.name)) {
      appStore.showToast(f.name + ' 类型不支持（支持PDF/Word/Excel/PPT/MD/CSV/TXT/代码/图片）', 'error')
      continue
    }
    valid.push(f)
  }
  return valid
}

const uploadFiles = async (files: File[]) => {
  const valid = validateFiles(Array.from(files))
  if (!valid.length) return
  uploading.value = true
  uploadProgress.value = { current: 0, total: valid.length }
  let successCount = 0
  try {
    for (const file of valid) {
      try {
        await knowledgeApi.uploadDoc(file)
        successCount++
      } catch (e: any) {
        appStore.showToast(file.name + ' 上传失败: ' + (e.response?.data?.detail || e.message), 'error')
      }
      uploadProgress.value.current++
    }
    if (successCount > 0) {
      appStore.showToast('✅ 成功上传 ' + successCount + '/' + valid.length + ' 个文档', 'success')
      await Promise.all([loadDocs(), loadStats()])
    }
  } finally {
    uploading.value = false
    uploadProgress.value = { current: 0, total: 0 }
  }
}

const handleUpload = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files?.length) return
  await uploadFiles(Array.from(files))
  input.value = ''
}

function onDragOver() {
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

const handleDrop = (e: DragEvent) => {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (!files?.length) return
  appStore.showToast('📎 检测到 ' + files.length + ' 个文件，开始上传...', 'info')
  uploadFiles(Array.from(files))
}

const handleReindexAll = async () => {
  if (!confirm('确定要全量重建所有文档的索引吗？这可能需要较长时间。')) return
  reindexingAll.value = true
  try {
    await knowledgeApi.reindexAll()
    appStore.showToast('✅ 全量重建索引任务已提交', 'success')
    setTimeout(() => loadStats(), 2000)
  } catch (e: any) {
    appStore.showToast('重建失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    reindexingAll.value = false
  }
}

const deleteDoc = async (id: number) => {
  if (!confirm('确定删除该文档？')) return
  try {
    await knowledgeApi.deleteDoc(id)
    appStore.showToast('🗑️ 文档已删除', 'success')
    selectedIds.value = selectedIds.value.filter(sid => sid !== id)
    await Promise.all([loadDocs(), loadStats()])
  } catch (e: any) {
    appStore.showToast('删除失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

const previewDoc = async (doc: KnowledgeDoc) => {
  previewVisible.value = true
  previewTitle.value = doc.title
  previewContent.value = ''
  previewLoading.value = true
  previewIsImage.value = false
  previewIsPdf.value = false
  previewImageUrl.value = ''
  previewPdfUrl.value = ''
  previewIsMeta.value = false
  previewMetaData.value = null

  const ext = (doc.doc_type || doc.title.split('.').pop() || '').toLowerCase()
  const isImg = ['png','jpg','jpeg','gif','webp','bmp','svg'].includes(ext)
  const isPdfFile = ext === 'pdf'

  if (isImg) {
    previewIsImage.value = true
    try {
      const res = await knowledgeApi.getFile(doc.id)
      previewImageUrl.value = URL.createObjectURL(res.data)
    } catch (e: any) {
      previewContent.value = '图片加载失败: ' + (e.response?.data?.detail || e.message)
    }
    previewLoading.value = false
    return
  }

  if (isPdfFile) {
    previewIsPdf.value = true
    try {
      const res = await knowledgeApi.getFile(doc.id)
      previewPdfUrl.value = URL.createObjectURL(res.data)
    } catch (e: any) {
      previewContent.value = 'PDF加载失败: ' + (e.response?.data?.detail || e.message)
    }
    previewLoading.value = false
    return
  }

  try {
    const res = await knowledgeApi.getDocContent(doc.id)
    const data = res.data as any
    if (data?.type === 'meta') {
      previewIsMeta.value = true
      previewMetaData.value = data
    } else if (data?.content) {
      previewContent.value = data.content
    } else if (data?.type === 'binary') {
      previewContent.value = data.message || `二进制文件 (${data.size} bytes)，请下载后查看`
    } else {
      previewContent.value = '该文档暂无可预览的内容'
    }
  } catch (e: any) {
    previewContent.value = '预览加载失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    previewLoading.value = false
  }
}

const formatSize = (bytes?: number) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

const formatDate = (iso: string) => {
  if (!iso) return '-'
  try {
    return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch { return '-' }
}

const getStatusClass = (s: string) => {
  if (s === 'success' || s === 'indexed') return 'bg-green-100 text-green-700'
  if (s === 'processing') return 'bg-yellow-100 text-yellow-700'
  if (s === 'error' || s === 'failed') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-600'
}

const getStatusLabel = (s: string) => {
  const map: Record<string, string> = { success: '已完成', indexed: '已索引', processing: '处理中', error: '失败', failed: '失败', pending: '等待中' }
  return map[s] || s || '未知'
}

onMounted(() => {
  loadDocs()
  loadStats()
})
</script>
