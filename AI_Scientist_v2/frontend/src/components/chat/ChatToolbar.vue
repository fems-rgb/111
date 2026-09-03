<template>
  <div class="chat-toolbar">
    <label class="tb-btn" title="上传文件">📎 <input type="file" multiple hidden @change="onFile" /></label>
    <button class="tb-btn" title="知识库检索" @click="$emit('kb-search')">🔍</button>
    <button class="tb-btn" title="流水线编排" @click="showPipeline=!showPipeline">⚙️</button>
    <button class="tb-btn" title="提交反馈触发迭代" @click="showFeedback=!showFeedback">🔄</button>
    <div v-if="showFeedback" class="fb-popover">
      <textarea v-model="feedbackText" placeholder="输入实验反馈或修正意见..." rows="3" />
      <button class="fb-submit" @click="doFeedback" :disabled="!feedbackText.trim()">提交反馈</button>
    </div>
    <div v-if="showPipeline" class="pipe-popover">
      <div class="pipe-title">流水线步骤（拖拽排序）</div>
      <div v-for="(step,idx) in localSteps" :key="step" class="pipe-step" draggable="true" @dragstart="dragIdx=idx" @dragover.prevent @drop="onDrop(idx)">
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
import { ref, watch } from 'vue'
import { submitFeedback } from '@/api/modules/hypothesis'

const props = defineProps<{ projectId: number; steps?: string[] }>()
const emit = defineEmits<{ (e:'files',files:File[]):void; (e:'kb-search'):void; (e:'pipeline-saved',steps:string[]):void; (e:'feedback-submitted'):void }>()

const showFeedback = ref(false)
const showPipeline = ref(false)
const feedbackText = ref('')
const localSteps = ref<string[]>([...(props.steps||['literature','hypothesis','design','experiment_plan','analysis','writing','review'])])
const newStep = ref('')
const dragIdx = ref(-1)
const availableAgents = ['literature','hypothesis','design','experiment_plan','analysis','writing','review','reflection']

watch(()=>props.steps,v=>{if(v)localSteps.value=[...v]})

function onFile(e:Event){const files=Array.from((e.target as HTMLInputElement).files||[]);if(files.length)emit('files',files)}
function addStep(){if(newStep.value&&!localSteps.value.includes(newStep.value)){localSteps.value.push(newStep.value);newStep.value=''}}
function onDrop(t:number){if(dragIdx.value<0||dragIdx.value===t)return;const item=localSteps.value.splice(dragIdx.value,1)[0];localSteps.value.splice(t,0,item);dragIdx.value=-1}
function savePipeline(){emit('pipeline-saved',[...localSteps.value]);showPipeline.value=false}
async function doFeedback(){if(!feedbackText.value.trim())return;try{await submitFeedback(props.projectId,{feedback:feedbackText.value});feedbackText.value='';showFeedback.value=false;emit('feedback-submitted')}catch(e){console.error('feedback failed',e)}}
</script>

<style scoped>
.chat-toolbar{display:flex;gap:4px;padding:6px 10px;border-top:1px solid #e5e7eb;background:#fff;position:relative;align-items:center}
.tb-btn{background:none;border:1px solid transparent;border-radius:6px;padding:4px 8px;cursor:pointer;font-size:16px;transition:all .15s}
.tb-btn:hover{background:#f0f4ff;border-color:#d0d7ff}
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
