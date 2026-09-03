<template>
  <div class="card">
    <h3 class="text-lg font-semibold mb-4">🖼️ AI图片学术分析</h3>

    <!-- 上传区域 -->
    <div v-if="!previewUrl"
         class="border-2 border-dashed border-surface-300 rounded-xl p-8 text-center hover:border-primary-400 hover:bg-primary-50/30 transition-all cursor-pointer"
         @click="($refs.fileInput as HTMLInputElement).click()"
         @dragover.prevent
         @drop.prevent="handleDrop">
      <span class="text-4xl block mb-3">📷</span>
      <p class="text-surface-600 font-medium">点击或拖拽上传图片</p>
      <p class="text-xs text-surface-400 mt-1">支持 JPG/PNG/WebP，最大10MB</p>
      <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleFileSelect" />
    </div>

    <!-- 预览 + 分析 -->
    <div v-else class="space-y-4">
      <div class="flex gap-4">
        <img :src="previewUrl" class="w-48 h-48 object-cover rounded-lg border border-surface-200" />
        <div class="flex-1 space-y-3">
          <textarea v-model="question" class="input-field h-20 resize-none" placeholder="你想了解这张图片的什么学术信息？"></textarea>
          <div class="flex gap-2">
            <button @click="analyze" :disabled="analyzing" class="btn-primary">
              {{ analyzing ? '分析中...' : '🔍 AI分析' }}
            </button>
            <button @click="reset" class="btn-secondary">重新上传</button>
          </div>
        </div>
      </div>

      <!-- 分析结果 -->
      <div v-if="result" class="p-4 bg-accent-50 rounded-lg border border-accent-200 animate-slide-up">
        <div class="flex justify-between items-center mb-2">
          <span class="font-medium text-accent-800">🤖 AI学术分析结果</span>
          <span class="text-xs text-accent-600">{{ result.model }} · ¥{{ result.cost?.toFixed(4) }}</span>
        </div>
        <MarkdownView :content="result.analysis" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import MarkdownView from './MarkdownView.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const previewUrl = ref('')
const question = ref('请从人文社科学术研究角度分析这张图片的内容和研究价值')
const analyzing = ref(false)
const result = ref<any>(null)
let selectedFile: File | null = null

function handleFileSelect(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) setFile(file)
}

function handleDrop(e: DragEvent) {
  const file = e.dataTransfer?.files?.[0]
  if (file) setFile(file)
}

function setFile(file: File) {
  if (!file.type.startsWith('image/')) {
    appStore.showToast('请上传图片文件', 'error')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    appStore.showToast('图片不能超过10MB', 'error')
    return
  }
  selectedFile = file
  previewUrl.value = URL.createObjectURL(file)
  result.value = null
}

async function analyze() {
  if (!selectedFile) return
  analyzing.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('question', question.value)
    const res = await axios.post('/api/v1/multimodal/analyze-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000
    })
    result.value = res.data
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '分析失败', 'error')
  } finally {
    analyzing.value = false
  }
}

function reset() {
  previewUrl.value = ''
  result.value = null
  selectedFile = null
}
</script>