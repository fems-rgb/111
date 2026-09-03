const fs = require("fs");
const c = [];
c.push(`<template>
  <div class="flex h-full">
    <div class="w-80 border-r border-surface-200 overflow-y-auto p-4">
      <h2 class="text-lg font-semibold mb-4">{{ $t('workspace.projects') }}</h2>
      <input v-model="searchQuery" type="text" :placeholder="$t('workspace.searchProjects')" class="w-full px-3 py-2 border border-surface-200 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-primary-300" />
      <div v-if="loading" class="text-center py-8 text-surface-400">{{ $t('common.loading') }}</div>
      <div v-else-if="filteredProjects.length === 0" class="text-center py-8 text-surface-400">{{ $t('workspace.noProjects') }}</div>
      <div v-else class="space-y-3">
        <div v-for="p in filteredProjects" :key="p.id" class="flex items-center justify-between p-4 rounded-lg border border-surface-100 hover:border-primary-200 hover:bg-primary-50/30 transition-all cursor-pointer group" @click="$router.push('/project/' + p.id)">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <h3 class="font-medium truncate">{{ p.title }}</h3>
              <StatusBadge :status="p.status" />
              <span v-if="p.hypothesis_count" class="text-xs bg-accent-100 text-accent-700 px-1.5 py-0.5 rounded">💡 {{ p.hypothesis_count }} {{ $t('workspace.hypotheses') }}</span>
            </div>
            <p class="text-sm text-surface-500 mt-1">{{ p.domain }} · {{ new Date(p.created_at).toLocaleDateString('zh-CN') }}</p>
          </div>
          <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button class="p-1.5 text-surface-400 hover:text-primary-600 rounded" @click.stop="handleStart(p.id)" :title="$t('workspace.start')">▶️</button>
            <button class="p-1.5 text-surface-400 hover:text-red-600 rounded" @click.stop="handleDelete(p.id)" :title="$t('common.delete')">🗑️</button>
          </div>
        </div>
      </div>
    </div>
    <div class="flex-1 flex flex-col">
      <div ref="chatContainer" class="flex-1 overflow-y-auto p-6 space-y-4">
        <div v-if="messages.length === 0" class="text-center text-surface-400 mt-20">
          <p class="text-4xl mb-4">🔬</p>
          <p>{{ $t('workspace.chatPlaceholder') }}</p>
        </div>
        <div v-for="(msg, idx) in messages" :key="idx" :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
          <div :class="['max-w-[70%] px-4 py-3 rounded-2xl', msg.role === 'user' ? 'bg-primary-600 text-white' : 'bg-surface-100 text-surface-800']">
            <div v-html="renderMarkdown(msg.content)"></div>
          </div>
        </div>
      </div>
      <div v-if="showAtMenu" class="mx-6 mb-2 border border-surface-200 rounded-lg bg-white shadow-lg max-h-48 overflow-y-auto">
        <div v-for="item in atSearchResults" :key="item.title" class="px-4 py-2 hover:bg-primary-50 cursor-pointer" @click="insertAtReference(item)">
          <span class="font-medium">{{ item.title }}</span>
          <span class="text-xs text-surface-400 ml-2">{{ item.source }}</span>
        </div>
        <div v-if="atSearchResults.length === 0" class="px-4 py-2 text-surface-400 text-sm">{{ $t('workspace.noResults') }}</div>
      </div>
      <div v-if="chatAttachments.length > 0" class="mx-6 mb-2 flex gap-2 flex-wrap">
        <div v-for="(file, idx) in chatAttachments" :key="idx" class="flex items-center gap-1 px-2 py-1 bg-surface-100 rounded text-sm">
          📎 {{ file.name }}
          <button class="text-surface-400 hover:text-red-500" @click="chatAttachments.splice(idx, 1)">×</button>
        </div>
      </div>
      <div class="p-4 border-t border-surface-200">
        <div class="flex gap-2">
          <label class="flex items-center px-3 py-2 cursor-pointer hover:bg-surface-100 rounded-lg">
            📎<input type="file" multiple class="hidden" @change="handleFileAttach" />
          </label>
          <textarea ref="inputRef" v-model="inputMessage" @keydown.enter.exact.prevent="sendMessage" @input="handleAtSearch" :placeholder="$t('workspace.inputPlaceholder')" rows="1" class="flex-1 px-4 py-2 border border-surface-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-300" />
          <button @click="sendMessageWithAttachments" :disabled="!inputMessage.trim() && chatAttachments.length === 0" class="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed">{{ $t('common.send') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/appStore'
import StatusBadge from '@/components/StatusBadge.vue'
import axios from 'axios'

const { t } = useI18n()
const router = useRouter()
const appStore = useAppStore()

interface Project {
  id: number; title: string; description: string; research_question: string
  domain: string; status: string; complexity: string | null; final_output: string
  review_score: number | null; tags: string[]; created_at: string; updated_at: string
  hypothesis_count?: number
}
interface Message { role: 'user' | 'assistant'; content: string }

const projects = ref<Project[]>([])
const searchQuery = ref('')
const loading = ref(false)
const filteredProjects = computed(() => {
  if (!searchQuery.value) return projects.value
  const q = searchQuery.value.toLowerCase()
  return projects.value.filter(p => p.title.toLowerCase().includes(q) || p.domain.toLowerCase().includes(q))
})

async function fetchProjects() {
  loading.value = true
  try { const { data } = await axios.get('/api/projects'); projects.value = data }
  catch (e: any) { appStore.showToast(e.response?.data?.detail || t('workspace.fetchFailed'), 'error') }
  finally { loading.value = false }
}

async function handleStart(id: number) {
  try { await axios.post(\`/api/projects/\${id}/start\`); appStore.showToast(t('workspace.startSuccess'), 'success'); await fetchProjects() }
  catch (e: any) { appStore.showToast(e.response?.data?.detail || t('workspace.startFailed'), 'error') }
}

async function handleDelete(id: number) {
  if (!confirm(t('workspace.confirmDelete'))) return
  try { await axios.delete(\`/api/projects/\${id}\`); appStore.showToast(t('workspace.deleteSuccess'), 'success'); await fetchProjects() }
  catch (e: any) { appStore.showToast(e.response?.data?.detail || t('workspace.deleteFailed'), 'error') }
}

const creating = ref(false)
const attachedFiles = ref<File[]>([])
async function createProject(newProject: Partial<Project>) {
  creating.value = true
  try {
    await axios.post('/api/projects', newProject)
    Object.assign(newProject, { title: '', research_question: '', description: '' })
    attachedFiles.value = []
    router.push('/project/')
  } catch (e: any) { appStore.showToast(e.response?.data?.detail || t('workspace.createFailed'), 'error') }
  finally { creating.value = false }
}

const messages = ref<Message[]>([])
const inputMessage = ref('')
const chatAttachments = ref<File[]>([])
const chatContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text) return
  messages.value.push({ role: 'user', content: text })
  inputMessage.value = ''
  await scrollToBottom()
  try { const { data } = await axios.post('/api/chat', { message: text }); messages.value.push({ role: 'assistant', content: data.reply || data.content || '' }) }
  catch { messages.value.push({ role: 'assistant', content: t('workspace.chatError') }) }
  await scrollToBottom()
}

async function sendMessageWithAttachments() {
  const hasAtt = chatAttachments.value.length > 0
  if (hasAtt) appStore.showToast(\`📎 \${t('workspace.uploadingFiles', { count: chatAttachments.value.length })}\`, 'info')
  await sendMessage()
  if (hasAtt) chatAttachments.value = []
}

function handleFileAttach(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files) chatAttachments.value.push(...Array.from(target.files))
  target.value = ''
}

async function scrollToBottom() { await nextTick(); if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight }

function renderMarkdown(content: string): string {
  return content.replace(/\\n/g, '<br/>').replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>').replace(/\`(.*?)\`/g, '<code>$1</code>')
}

const showAtMenu = ref(false)
const atSearchQuery = ref('')
const atSearchResults = ref<{ title: string; source: string }[]>([])

function handleAtSearch() {
  const val = inputMessage.value; const atIdx = val.lastIndexOf('@')
  if (atIdx >= 0 && showAtMenu.value) atSearchQuery.value = val.slice(atIdx + 1).split(/\\s/)[0]
  else if (atIdx < 0) showAtMenu.value = false
}

function insertAtReference(item: { title: string; source: string }) {
  const val = inputMessage.value; const atIdx = val.lastIndexOf('@')
  if (atIdx >= 0) inputMessage.value = val.slice(0, atIdx) + \`[\${item.title}](\${item.source}) \` + val.slice(atIdx + 1 + atSearchQuery.value.length)
  showAtMenu.value = false
}

onMounted(() => { fetchProjects() })
</script>`);
fs.writeFileSync('src/views/workspace/ChatView.vue', c.join('\n'), 'utf8');
console.log('✅ ChatView.vue created successfully');