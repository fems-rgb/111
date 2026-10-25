<template>
  <div class="chat-toolbar" @dragover.prevent="dragOver=true" @dragleave="dragOver=false" @drop.prevent="onDrop">
    <label class="tb-btn" title="上传文件" v-if="isExpert">
      📎 <input type="file" multiple hidden @change="onFile" accept=".pdf,.docx,.doc,.csv,.xlsx,.png,.jpg,.jpeg,.webp,.mp4,.wav,.mp3,.txt,.md" />
    </label>
    <button v-if="isExpert" class="tb-btn" title="知识库检索" @click="$emit('kb-search')">🔍</button>
    <button v-if="isExpert" class="tb-btn" title="流水线编排" @click="showPipeline=!showPipeline">⚙️</button>
    <button v-if="isExpert" class="tb-btn" title="提交反馈触发迭代" @click="showFeedback=!showFeedback">🔄</button>
    <button v-if="isExpert" class="tb-btn" title="粘贴图片" @click="triggerPaste">🖼️</button>

    <!-- 拖拽提示 -->
    <div v-if="dragOver" class="drop-hint">📂 释放以上传文件</div>

    <!-- 已上传文件列表 -->
    <div v-if="uploadedFiles.length" class="file-chips">
      <span v-for="f in uploadedFiles" :key="f.id" class="file-chip" :title="f.name">
        {{ fileIcon(f.ext) }} {{ f.name.slice(0, 18) }}<span v-if="f.status==='uploading'"> ⏳</span><span v-else-if="f.status==='done'"> ✅</span><span v-else-if="f.status==='error'"> ❌</span>
      </span>
    </div>

    <div v-if="showFeedback" class="fb-popover">
      <textarea v-model="feedbackText" placeholder="输入实验反馈或修正意见..." rows="3" />
      <button class="fb-submit" @click="doFeedback" :disabled="!feedbackText.trim()">提交反馈</button>
    </div>
    <div v-if="showPipeline" class="pipe-popover">
      <div class="pipe-title">流水线步骤（拖拽排序）</div>
      <div v-for="(step,idx) in localSteps" :key="step" class="pipe-step" draggable="true" @dragstart="dragIdx=idx" @dragover.prevent @drop="onStepDrop(idx)">
        <span class="pipe-drag">☰</span> {{ step }}
        <button class="pipe-rm" @click="localSteps.splice(idx,1)">✕</button>
      </div>
      <div class="pipe-add">
        <select v-model="newStep"><option value="">+ 添加Agent</option><option v-for="a in availableAgents" :key="a" :value="a">{{ a }}</option></select>
        <button @click="addStep">添加</button>
      </div>
      <button class="pipe-save" @click="savePipeline">保存流水线</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { submitFeedback } from '@/api/modules/hypothesis'
import { uploadApi } from '@/api/modules/chat'
import { useAppStore } from '@/stores/app'

const props = defineProps<{ projectId: number; steps?: string[] }>()
const emit = defineEmits<{
  (e:'files',files:File[]):void
  (e:'attachments-uploaded', items: Array<{ file_id: string; filename: string; summary: string }>):void
  (e:'kb-search'):void
  (e:'pipeline-saved',steps:string[]):void
  (e:'feedback-submitted'):void
}>()

const appStore = useAppStore()
const { mode } = storeToRefs(appStore)
const isExpert = computed(() => mode.value === 'expert')

const showFeedback = ref(false)
const showPipeline = ref(false)
const feedbackText = ref('')
const localSteps = ref<string[]>([...(props.steps||['literature','hypothesis','design','experiment_plan','analysis','writing','review'])])
const newStep = ref('')
const dragIdx = ref(-1)
const dragOver = ref(false)
const availableAgents = ['literature','hypothesis','design','experiment_plan','analysis','writing','review','reflection']

interface FileChip { id: number; name: string; ext: string; status: 'uploading'|'done'|'error'; file_id?: string; summary?: string }
const uploadedFiles = ref<FileChip[]>([])
let chipId = 0

watch(()=>props.steps,v=>{if(v)localSteps.value=[...v]})

function fileIcon(ext: string): string {
  const map: Record<string,string> = { pdf:'📄', doc:'📝', docx:'📝', csv:'📊', xlsx:'📊', png:'🖼️', jpg:'🖼️', jpeg:'🖼️', webp:'🖼️', mp4:'🎬', wav:'🎵', mp3:'🎵', txt:'📃', md:'📃' }
  return map[ext?.toLowerCase()] || '📎'
}

async function doUpload(files: File[]) {
  const readyItems: Array<{ file_id: string; filename: string; summary: string }> = []
  for (const file of files) {
    const ext = file.name.split('.').pop() || ''
    const chip: FileChip = { id: ++chipId, name: file.name, ext, status: 'uploading' }
    uploadedFiles.value.push(chip)
    try {
      const CHUNK_SIZE = 2 * 1024 * 1024
      const totalChunks = Math.ceil(file.size / CHUNK_SIZE)
      const initRes = await uploadApi.init(file.name, file.size, file.type)
      const uploadId = initRes.data.upload_id
      for (let i = 0; i < totalChunks; i++) {
        const start = i * CHUNK_SIZE
        const blob = file.slice(start, Math.min(start + CHUNK_SIZE, file.size))
        await uploadApi.uploadChunk(uploadId, i, '', blob)
      }
      const completeRes = await uploadApi.complete(uploadId)
      const data = completeRes.data || {}
      chip.status = 'done'
      chip.file_id = data.file_id
      chip.summary = data.summary
      readyItems.push({ file_id: data.file_id, filename: data.filename || file.name, summary: data.summary || '' })
    } catch (e: any) {
      chip.status = 'error'
      console.warn('[Upload] failed:', file.name, e?.message)
    }
  }
  if (readyItems.length) emit('attachments-uploaded', readyItems)
  emit('files', files)
}

function onFile(e: Event) {
  const files = Array.from((e.target as HTMLInputElement).files || [])
  if (files.length) doUpload(files)
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length) doUpload(files)
}

function triggerPaste() {
  navigator.clipboard.read?.().then(async (items) => {
    for (const item of items) {
      if (item.types.includes('image/png')) {
        const blob = await item.getType('image/png')
        const file = new File([blob], `paste_${Date.now()}.png`, { type: 'image/png' })
        doUpload([file])
        return
      }
    }
  }).catch(() => appStore.showToast('剪贴板无图片', 'error'))
}

function _pasteHandler(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) { doUpload([file]); e.preventDefault(); return }
    }
  }
}
onMounted(() => document.addEventListener('paste', _pasteHandler))
onUnmounted(() => document.removeEventListener('paste', _pasteHandler))

function addStep(){if(newStep.value&&!localSteps.value.includes(newStep.value)){localSteps.value.push(newStep.value);newStep.value=''}}
function onStepDrop(t:number){if(dragIdx.value<0||dragIdx.value===t)return;const item=localSteps.value.splice(dragIdx.value,1)[0];localSteps.value.splice(t,0,item);dragIdx.value=-1}
function savePipeline(){emit('pipeline-saved',[...localSteps.value]);showPipeline.value=false}
async function doFeedback(){if(!feedbackText.value.trim())return;try{await submitFeedback(props.projectId,{feedback:feedbackText.value});feedbackText.value='';showFeedback.value=false;emit('feedback-submitted')}catch(e){console.error('feedback failed',e)}}
</script>

<style scoped>
.chat-toolbar{display:flex;gap:4px;padding:6px 10px;border-top:1px solid #e5e7eb;background:#fff;position:relative;align-items:center;flex-wrap:wrap}
.tb-btn{background:none;border:1px solid transparent;border-radius:6px;padding:4px 8px;cursor:pointer;font-size:16px;transition:all .15s}
.tb-btn:hover{background:#f0f4ff;border-color:#d0d7ff}
.drop-hint{position:absolute;inset:0;background:rgba(26,115,232,.08);border:2px dashed #1a73e8;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;color:#1a73e8;font-weight:600;z-index:10}
.file-chips{display:flex;gap:4px;flex-wrap:wrap;margin-left:8px}
.file-chip{font-size:11px;padding:2px 8px;background:#f0f4ff;border-radius:12px;color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:160px}
.fb-popover,.pipe-popover{position:absolute;bottom:44px;left:10px;background:#fff;border:1px solid #e5e7eb;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,.1);padding:12px;z-index:100;min-width:300px}
.fb-popover textarea{width:100%;resize:vertical;border:1px solid #ddd;border-radius:6px;padding:8px;font-size:13px;box-sizing:border-box}
.fb-submit{margin-top:8px;padding:6px 16px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px}
.fb-submit:disabled{opacity:.5;cursor:not-allowed}
.pipe-title{font-weight:700;font-size:13px;margin-bottom:8px}
.pipe-step{display:flex;align-items:center;gap:6px;padding:5px 8px;background:#f8f9fa;border-radius:6px;margin-bottom:4px;font-size:13px;cursor:grab}
.pipe-drag{color:#aaa}
.pipe-rm{margin-left:auto;background:none;border:none;color:#ccc;cursor:pointer;font-size:14px}
.pipe-rm:hover{color:#e74c3c}
.pipe-add{display:flex;gap:4px;margin-top:6px}
.pipe-add select{flex:1;padding:4px 8px;border:1px solid #ddd;border-radius:6px;font-size:13px}
.pipe-add button{padding:4px 12px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px}
.pipe-save{margin-top:8px;width:100%;padding:6px;background:#34a853;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px}
</style>
