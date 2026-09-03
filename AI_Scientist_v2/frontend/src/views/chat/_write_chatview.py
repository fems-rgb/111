import pathlib

content = r'''<template>
  <div class="flex flex-col h-[calc(100vh-8rem)] animate-fade-in">
    <div class="card flex-1 flex flex-col overflow-hidden relative">
      <!-- 顶部工具栏 -->
      <div class="flex items-center justify-between mb-4 px-4 pt-2">
        <h2 class="text-lg font-semibold">💬 AI智能对话</h2>
        <div class="flex items-center gap-3">
          <span class="text-xs text-surface-500">模式</span>
          <button @click="runMode = runMode === 'quick' ? 'expert' : 'quick'"
                  :class="['px-3 py-1 rounded-full text-xs font-medium transition-colors',
                           runMode === 'expert' ? 'bg-primary-600 text-white' : 'bg-surface-200 text-surface-600']">
            {{ runMode === 'expert' ? '🔬 专家模式' : '⚡ 快速模式' }}
          </button>
          <div class="w-px h-4 bg-surface-200 mx-1"></div>
          <button @click="clearChat" class="btn-secondary text-sm px-3 py-1.5">🗑️ 新对话</button>
          <button @click="loadHistory" :disabled="loadingHistory" class="btn-secondary text-sm px-3 py-1.5">
            {{ loadingHistory ? '加载中...' : '📜 历史记录' }}
          </button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div ref="msgContainer" class="flex-1 overflow-y-auto space-y-4 mb-4 px-4 pr-2"
           @paste="handlePaste">
        <div v-if="messages.length === 0" class="text-center py-12 text-surface-400">
          <span class="text-4xl block mb-3">💬</span>
          <p>{{ historyLoaded ? '暂无历史消息' : '点击「历史记录」加载过往对话，或直接开始新对话' }}</p>
          <p class="text-xs mt-2 text-surface-300">💡 拖拽 / Ctrl+V 粘贴文件到对话区域即可上传附件</p>
        </div>
        <div v-for="msg in messages" :key="msg.id"
             :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
          <div :class="['max-w-[80%] rounded-2xl px-4 py-3',
                        msg.role === 'user' ? 'bg-primary-600 text-white' : 'bg-surface-100 text-surface-800']">
            <template v-if="msg.role === 'user'">
              <div v-if="(msg as any).attachments?.length" class="mb-2 space-y-1.5">
                <div v-for="(att, ai) in (msg as any).attachments" :key="ai"
                     class="flex items-center gap-2 bg-white/20 rounded-lg px-2 py-1.5 text-xs max-w-full">
                  <img v-if="isImage(att.name)" :src="att.previewUrl || att.url"
                       class="w-10 h-10 object-cover rounded border border-white/30 cursor-pointer hover:scale-110 transition-transform"
                       @click="openPreview(att)" />
                  <div v-else-if="isPdf(att.name)" class="w-10 h-10 bg-red-100 rounded flex items-center justify-center text-red-600 font-bold text-[10px] border border-white/30">
                    PDF
                  </div>
                  <span v-else class="w-10 h-10 bg-white/30 rounded flex items-center justify-center text-lg">📄</span>
                  <div class="flex-1 min-w-0">
                    <p class="truncate font-medium">{{ att.name }}</p>
                    <div v-if="att.progress !== undefined && att.progress < 100" class="flex items-center gap-1.5 mt-0.5">
                      <div class="h-1.5 flex-1 bg-black/20 rounded-full overflow-hidden">
                        <div class="h-full bg-white/90 rounded-full transition-all duration-200"
                             :style="{ width: att.progress + '%' }"></div>
                      </div>
                      <span class="w-8 text-right tabular-nums">{{ att.progress }}%</span>
                    </div>
                    <span v-else-if="att.progress === 100" class="text-green-300 text-[10px]">✓ 已上传</span>
                    <span v-else-if="att.error" class="text-red-300 text-[10px]">✗ 上传失败
                      <button @click.stop="retryUpload(msg, ai)" class="ml-1 underline hover:text-white">重试</button>
                    </span>
                  </div>
                </div>
              </div>
              <p class="whitespace-pre-wrap">{{ msg.content }}</p>
              <div v-if="(msg as any).sendStatus === 'sending'" class="mt-1 text-[10px] opacity-70 flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>发送中...
              </div>
              <div v-else-if="(msg as any).sendStatus === 'failed'" class="mt-1 text-[10px] text-red-300">发送失败</div>
            </template>
            <MarkdownView v-else :content="msg.content" />
            <p class="text-xs mt-1 opacity-60">{{ new Date(msg.created_at).toLocaleTimeString('zh-CN') }}</p>
          </div>
        </div>
        <div v-if="sseConnected" class="flex justify-start">
          <div class="bg-green-50 border border-green-200 rounded-xl px-3 py-2 text-xs text-green-700 flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            SSE 实时推送已连接
          </div>
        </div>
      </div>

      <!-- 多模态文件传输中枢 -->
      <div class="border-t border-surface-100 bg-surface-50/50 px-4 py-2 flex items-center gap-3 text-sm min-h-[60px]"
           @dragover.prevent="dragOver = true"
           @dragleave.self="dragOver = false"
           @drop.prevent="handleChatDrop"
           @paste="handlePaste"
           :class="{ 'bg-primary-50 ring-2 ring-primary-300': dragOver }">
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <span class="text-surface-400 shrink-0">📎</span>
          <div v-if="chatAttachments.length === 0" class="text-surface-400 truncate">
            拖拽 / Ctrl+V 粘贴文件，或输入 <kbd class="px-1 py-0.5 bg-white rounded border text-xs font-mono">@</kbd> 引用资料库
          </div>
          <div v-else class="flex flex-wrap gap-1.5">
            <span v-for="(f, i) in chatAttachments" :key="i"
                  class="inline-flex items-center gap-1 bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full text-xs max-w-[200px]">
              <img v-if="isImage(f.name) && f.previewUrl" :src="f.previewUrl" class="w-4 h-4 rounded object-cover" />
              <span v-else-if="isPdf(f.name)" class="text-red-600 font-bold text-[10px]">PDF</span>
              <span class="truncate">{{ f.name }}</span>
              <button @click="chatAttachments.splice(i, 1)" class="hover:text-red-600 font-bold">×</button>
            </span>
          </div>
        </div>
        <button v-if="chatAttachments.length > 0" @click="chatAttachments = []"
                class="text-xs text-surface-400 hover:text-red-500 shrink-0">清空</button>
      </div>

      <!-- 输入框 -->
      <div class="flex gap-3 p-4 border-t border-surface-100">
        <input v-model="inputText" class="input-field flex-1" placeholder="输入问题，Ctrl+V粘贴文件，@ 引用资料库..." @keyup.enter="handleSend" />
        <button @click="handleSend" :disabled="sending" class="btn-primary">
          {{ sending ? '...' : '发送' }}
        </button>
      </div>
    </div>

    <!-- 全屏预览弹窗 -->
    <teleport to="body">
      <div v-if="previewItem" class="fixed inset-0 z-[100] bg-black/70 flex items-center justify-center p-8" @click.self="previewItem = null">
        <div class="relative max-w-5xl max-h-[90vh] bg-white rounded-xl overflow-hidden shadow-2xl">
          <button @click="previewItem = null" class="absolute top-3 right-3 z-10 w-8 h-8 bg-black/50 text-white rounded-full flex items-center justify-center hover:bg-black/70">×</button>
          <img v-if="isImage(previewItem.name)" :src="previewItem.previewUrl || previewItem.url" class="max-w-full max-h-[85vh] object-contain" />
          <iframe v-else-if="isPdf(previewItem.name)" :src="previewItem.url" class="w-[80vw] h-[85vh]" />
          <div v-else class="p-12 text-center text-surface-500">
            <span class="text-4xl block mb-3">📄</span>
            <p>{{ previewItem.name }}</p>
            <p class="text-sm mt-2">此文件类型暂不支持在线预览</p>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onUnmounted } from 'vue'
import { chatApi, uploadApi } from '@/api/modules/chat'
import client from '@/api/client'
import { useAppStore } from '@/stores/app'
import MarkdownView from '@/components/common/MarkdownView.vue'
import type { ChatMessage } from '@/types'

const appStore = useAppStore()
const messages = ref<any[]>([])
const inputText = ref('')
const sending = ref(false)
const runMode = ref<'quick' | 'expert'>('quick')
const loadingHistory = ref(false)
const historyLoaded = ref(false)
const msgContainer = ref<HTMLElement | null>(null)

function isImage(name: string) { return /\.(png|jpg|jpeg|gif|webp|bmp|svg)$/i.test(name) }
function isPdf(name: string) { return /\.pdf$/i.test(name) }

const previewItem = ref<any>(null)
function openPreview(att: any) { previewItem.value = att }

const dragOver = ref(false)
const chatAttachments = ref<Array<{
  name: string; file?: File; type?: string; summary?: string; file_id?: string;
  progress?: number; error?: boolean; previewUrl?: string; url?: string;
  uploadId?: string; retryCount?: number
}>>([])

const ALLOWED_EXTS = /\.(pdf|csv|md|txt|png|jpg|jpeg|xlsx|xls|docx|doc|pptx|gif|webp)$/i
const MAX_SIZE = 50 * 1024 * 1024
const CHUNK_THRESHOLD = 2 * 1024 * 1024

function addFiles(files: FileList | File[]) {
  let added = 0
  for (let i = 0; i < files.length; i++) {
    const f = files[i]
    if (f.size > MAX_SIZE) { appStore.showToast(f.name + ' 超过50MB限制', 'error'); continue }
    if (!ALLOWED_EXTS.test(f.name)) { appStore.showToast(f.name + ' 类型不支持', 'error'); continue }
    const entry: any = { name: f.name, file: f, type: f.type, progress: undefined }
    if (isImage(f.name)) { entry.previewUrl = URL.createObjectURL(f) }
    chatAttachments.value.push(entry)
    added++
  }
  if (added > 0) appStore.showToast('📎 已添加 ' + added + ' 个附件', 'success')
}

function handleChatDrop(e: DragEvent) {
  dragOver.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) addFiles(files)
}

function handlePaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  const files: File[] = []
  for (let i = 0; i < items.length; i++) {
    if (items[i].kind === 'file') {
      const f = items[i].getAsFile()
      if (f) files.push(f)
    }
  }
  if (files.length > 0) { e.preventDefault(); addFiles(files) }
}

async function computeSHA256(blob: Blob): Promise<string> {
  const buffer = await blob.arrayBuffer()
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

async function smartUpload(att: any, onProgress: (pct: number) => void): Promise<any> {
  const file = att.file
  if (!file) throw new Error('无文件')

  if (file.size <= CHUNK_THRESHOLD) {
    const res = await uploadApi.directUpload(file, '')
    onProgress(100)
    return res.data
  }

  const initRes = await uploadApi.init(file.name, file.size, file.type)
  const uploadId = initRes.data.upload_id
  const chunkSize = initRes.data.chunk_size
  att.uploadId = uploadId

  let startChunk = 0
  try {
    const statusRes = await uploadApi.getStatus(uploadId)
    const uploaded = statusRes.data.uploaded_chunks || []
    if (uploaded.length > 0) {
      startChunk = Math.max(...uploaded) + 1
      appStore.showToast('📎 ' + file.name + ' 从第' + startChunk + '片续传', 'info')
    }
  } catch (_e) { /* 新上传 */ }

  const totalChunks = Math.ceil(file.size / chunkSize)
  for (let i = startChunk; i < totalChunks; i++) {
    const start = i * chunkSize
    const end = Math.min(start + chunkSize, file.size)
    const chunk = file.slice(start, end)
    const hash = await computeSHA256(chunk)
    await uploadApi.uploadChunk(uploadId, i, hash, chunk)
    onProgress(Math.round(((i + 1) / totalChunks) * 100))
  }

  const completeRes = await uploadApi.complete(uploadId, '')
  return completeRes.data
}

async function retryUpload(msg: any, attIndex: number) {
  const att = msg.attachments[attIndex]
  if (!att) return
  att.error = false
  att.progress = 0
  att.retryCount = (att.retryCount || 0) + 1

  const chatAtt = chatAttachments.value.find(a => a.name === att.name && a.file)
  if (!chatAtt?.file) {
    appStore.showToast('原始文件已不在本地，请重新添加', 'error')
    return
  }

  try {
    const result = await smartUpload(chatAtt, (pct) => { att.progress = pct })
    att.progress = 100
    att.file_id = result.file_id
    att.summary = result.summary
    appStore.showToast('✅ ' + att.name + ' 重试成功', 'success')
  } catch (e: any) {
    att.error = true
    att.progress = 0
    appStore.showToast(att.name + ' 重试失败: ' + (e.message || '未知错误'), 'error')
  }
}

async function loadHistory() {
  if (loadingHistory.value) return
  loadingHistory.value = true
  try {
    const res = await chatApi.history(undefined, 50)
    messages.value = [...res.data].sort((a: any, b: any) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    historyLoaded.value = true
    scrollToBottom()
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '加载历史失败', 'error')
  } finally { loadingHistory.value = false }
}

function clearChat() {
  messages.value = []
  historyLoaded.value = false
}

async function handleSend() {
  const text = inputText.value.trim()
  const hasAttachments = chatAttachments.value.length > 0
  if ((!text && !hasAttachments) || sending.value) return

  inputText.value = ''
  sending.value = true

  const tempMsg: any = {
    id: Date.now(), project_id: null, user_id: 0,
    role: 'user', content: text, content_type: 'text', tokens_used: 0,
    created_at: new Date().toISOString(),
    sendStatus: 'sending',
    attachments: hasAttachments ? chatAttachments.value.map(a => ({
      name: a.name, progress: 0, previewUrl: a.previewUrl, url: a.url
    })) : undefined
  }
  messages.value.push(tempMsg)
  scrollToBottom()

  try {
    const uploadResults: Array<{ file_id: string; name: string; summary: string }> = []
    if (hasAttachments) {
      const uploads = chatAttachments.value.map(async (att, idx) => {
        if (!att.file) return null
        try {
          const result = await smartUpload(att, (pct) => {
            if (tempMsg.attachments) {
              tempMsg.attachments[idx].progress = pct
              scrollToBottom()
            }
          })
          if (tempMsg.attachments) tempMsg.attachments[idx].progress = 100
          uploadResults.push({ file_id: result.file_id, name: att.name, summary: result.summary })
          return result
        } catch (e: any) {
          if (tempMsg.attachments) tempMsg.attachments[idx].error = true
          appStore.showToast(att.name + ' 上传失败: ' + (e.message || '未知错误'), 'error')
          return null
        }
      })
      await Promise.all(uploads)
    }

    const attachmentPayload = uploadResults.filter(Boolean)
    const sendBody = attachmentPayload.length > 0
      ? text + '\n\n[attachments:' + JSON.stringify(attachmentPayload) + ']'
      : text

    const res = await chatApi.send(sendBody)
    tempMsg.sendStatus = 'sent'
    chatAttachments.value = []

    const aiMsg: any = {
      id: Date.now() + 1, project_id: null, user_id: 0,
      role: 'assistant', content: res.data.reply, content_type: 'markdown',
      tokens_used: res.data.tokens.input + res.data.tokens.output,
      created_at: new Date().toISOString()
    }
    messages.value.push(aiMsg)
    scrollToBottom()
  } catch (e: any) {
    tempMsg.sendStatus = 'failed'
    appStore.showToast(e.response?.data?.detail || '发送失败', 'error')
  } finally {
    sending.value = false
  }
}

function scrollToBottom() {
  nextTick(() => { if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight })
}

const sseConnected = ref(false)
let abortController: AbortController | null = null

async function connectPlanSSE() {
  if (abortController) return
  abortController = new AbortController()
  const token = localStorage.getItem('token') || ''
  try {
    const response = await fetch('/api/v1/stream/events', {
      method: 'GET',
      headers: { 'Authorization': 'Bearer ' + token, 'Accept': 'text/event-stream' },
      signal: abortController.signal
    })
    if (!response.ok) throw new Error('SSE连接失败: ' + response.status)
    if (!response.body) throw new Error('响应体为空')
    sseConnected.value = true
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            messages.value.push({
              id: Date.now() + Math.random(), project_id: null, user_id: 0,
              role: 'assistant',
              content: '📋 **计划节点更新** [' + (data.node_id || '') + ']\n\n操作: ' + (data.action || '') + ' → 状态: ' + (data.status || ''),
              content_type: 'markdown', tokens_used: 0, created_at: new Date().toISOString()
            })
            scrollToBottom()
          } catch (e) { console.error('[SSE] 解析失败:', e) }
        }
      }
    }
  } catch (e: any) {
    if (e.name !== 'AbortError') {
      sseConnected.value = false
      setTimeout(() => { abortController = null; connectPlanSSE() }, 5000)
    }
  }
}

function disconnectPlanSSE() {
  abortController?.abort()
  abortController = null
  sseConnected.value = false
}

onUnmounted(() => disconnectPlanSSE())
</script>
'''

pathlib.Path(r'D:\AI_Scientist\AI_Scientist\frontend\src\views\chat\ChatView.vue').write_text(content, encoding='utf-8')
print('OK: ChatView.vue written successfully')
