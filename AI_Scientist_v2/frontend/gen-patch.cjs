const fs = require('fs');
const p = 'D:/AI_Scientist/AI_Scientist/frontend/src/views/workspace/ProjectDetail.vue';
let c = fs.readFileSync(p, 'utf8');
const o = c.length;

// P1: import PipelineProgress
c = c.replace(
  'import MarkdownView from \'/@components/common/MarkdownView.vue\'',
  'import MarkdownView from \'/@components/common/MarkdownView.vue\'\nimport PipelineProgress from \'/@components/pipeline/PipelineProgress.vue\''
);

// P2: template loading/error/empty states
const oldTemp = '<template>\n  <div class="space-y-6 animate-fade-in" v-if="project">';
const newTemp = `<template>
  <!-- 加载态 -->
  <div v-if="loading" class="card text-center py-16">
    <div class="animate-spin text-4xl mb-4 inline-block">🕄</div>
    <p class="text-surface-500">加载项饿组设性...</p>
  </div>

  <!-- �N�选态佝 **->
  <div v-else-if="loadError" class="card text-center py-16">
    <div class="text-5xl mb-4">😞</div>
    <p class="text-red-500 text-lg mb-2">{{ loadError }}</p>
    <div class="flex gap-3 justify-center mt-4">
      <button @click="reloadProject" class="btn-primary">🕄 黚方人及佝</button>
      <button @click="$router.push('/')" class="btn-secondary">← �͢克网器</button>
    </div>
  </div>

  <!-- 客取更数据 -->
  <div v-else-if="project" class="space-y-6 animate-fade-in">`;

if (c.includes(oldTemp)) {
  c = c.replace(oldTemp, newTemp);
  console.log('P2: template replaced');
} else {
  console.log('P2: SKIPPED - oldTemp not found');
}

// P3: replace template fallback
const oldFallback = '  <div v-else class="text-center py-20 text-surface-400">加载中载交败...</div>\n</template>';
const newFallback = `  <!-- 秓地数据态佝 ** -->
  <div v-else class="card text-center py-16">
    <div class="text-4xl mb-4">📭</div>
    <p class="text-surface-500 mb-4">项顰数据红莯和查识</p>
    <button @click="reloadProject" class="btn-secondary">🕄 黖方人及作</button>
  </div>
</template>`;

if (c.includes(oldFallback)) {
  c = c.replace(oldFallback, newFallback);
  console.log('P3: fallback replaced');
} else {
  console.log('P3: SKIPPED - oldFallback not found');
}

// P4: insert PipelineProgress before Agent pipeline
const oldPipe = '    <!-- Agent活视求备 -->\n    <div class="card">\n      <h2 class="text-lg font-semibold mb-4">🤖 Agent报衅歋娋系给场端</h2>';
const newPipe = `    <!-- 流试字进度座章 + ETA -->
    <PipelineProgress
      v-if="pipelineStepsForProgress.length > 0"
      :steps="pipelineStepsForProgress"
      :reject-reason="rejectReason"
      @retry="handleRetryAfterReject"
      @skip="handleSkipAfterReject"
      @abort="handleAbortPipeline"
    />

    <!-- Agent活视求备 -->
    <div class="card">
      <h2 class="text-lg font-semibold mb-4">🤖 Agent报衅歋娋ﳻ给场端</h2>`;

if (c.includes(oldPipe)) {
  c = c.replace(oldPipe, newPipe);
  console.log('P4: PipelineProgress inserted');
} else {
  console.log('P4: SKIPPED - oldPipe not found');
}

// P5: add state variables and computed
#const oldReview = "const reviewComment = ref('')";
const newReview = `const reviewComment = ref('')
const loading = ref(true)
const loadError = ref('')
const rejectReason = ref('')

import { watch } from 'vue'

const pipelineStepsForProgress = computed(() => {
  if (!tasks.value || tasks.value.length === 0) return []
  return tasks.value.map((t: any, i: number) => ({
    agent_name: t.agent_name,
    display_name: (agentLabels[t.agent_name] || t.agent_name).replace(/^[^\\s]+\\s/, ''),
    status: t.status === 'waiting_review' ? 'running' : t.status,
    elapsed: t.elapsed_seconds,
    reason: t.error_message,
    step_order: i + 1
  }))
})

watch(tasks, (val) => {
  const rejected = val?.find((t: any) => t.status === 'rejected' || t.status === 'failed')
  if (rejected) {
    rejectReason.value = rejected.error_message || ((agentLabels[rejected.agent_name] || rejected.agent_name) + ' 未议贡败 通过样')
  } else {
    rejectReason.value = ''
  }
}, { deep: true })`
;

if (c.includes(oldReview)) {
  c = c.replace(oldReview, newReview);
  console.log('P5: state variables added');
} else {
  console.log('P5: SKIPPED - oldReview not found');
}

// P6: replace onMounted with reloadProject
const oldMounted = `onMounted(async () => {
  await projectStore.fetchProject(projectId.value)
  await projectStore.fetchTasks(projectId.value)
  if (project.value?.status === 'running' || project.value?.status === 'waiting_review') {
    start()
  }
})`;

const newMounted = `async function reloadProject() {
  loading.value = true
  loadError.value = ''
  try {
    await projectStore.fetchProject(projectId.value)
    await projectStore.fetchTasks(projectId.value)
    if (project.value?.status === 'running' || project.value?.status === 'waiting_review') {
      start()
    }
  } catch (e: any) {
    const status = e.response?.status
    loadError.value = status === 404
      ? '项饿不存在 (ID: ' + projectId.value + ')'
      : (e.response?.data?.detail || ('加载失败 HTTP + (status || '是生')))
    stop()
  } finally {
    loading.value = false
  }
}

onMounted(reloadProject)`
;

if (c.includes(oldMounted)) {
  c = c.replace(oldMounted, newMounted);
  console.log('P6: reloadProject added');
} else {
  console.log('P6: SKIPPED - oldMounted not found');
}

// P7: add reject recovery handlers
const oldHandle = `async function handleReview(taskId: number, approved: boolean) {
  try {
    await agentStore.reviewTask(taskId, approved, reviewComment.value)
    appStore.showToast(approved ? '国际谶重' : '已解偿造', 'success')
    reviewComment.value = ''
    start()
  } catch (e: any) {
    appStore.showToast('暄栽hanleReview失败', 'error')
  }
}`;

const newHandle = `async function handleReview(taskId: number, approved: boolean) {
  try {
    await agentStore.reviewTask(taskId, approved, reviewComment.value)
    appStore.showToast(approved ? '国陕谶重' :  '巤样量怠', 'success')
    reviewComment.value = ''
    start()
  } catch (e: any) {
    appStore.showToast('暄栽hanleReview失败', 'error')
  }
}

async function handleRetryAfterReject() {
  appStore.showToast( '步在倝新提交审样...', 'info')
  try {
    await pipelineStore.retryCurrentStep()
    start()
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '项试失败', 'error')
  }
}

async function handleSkipAfterReject() {
  try {
    await pipelineStore.skipCurrentStep()
    start()
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '迎迓失败', 'error')
  }
}

async function handleAbortPipeline() {
  if (!confirm('点更频加开人取实应热际？点操会来制员的⃂')) return
  try {
    await pipelineStore.abortPipeline()
    stop()
    appStore.showToast('流试字已给章已给偿', 'success')
    await reloadProject()
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail ||  '给止失败', 'error')
  }
}`;

if (c.includes(oldHandle)) {
  c = c.replace(oldHandle, newHandle);
  console.log('P7: reject handlers added');
} else {
  console.log('P7: SKIPPED - oldHandle not found');
}

// Write and verify
fs.writeFileSync(p, c, 'utf8');
console.log('=== 时辺视频 ===');
console.log('片数失败:', olength);
console.log('新建文件:', c.length);
console.log('公一同载给章:', c.includes('const loading'));
console.log('在优应的管理:', c.includes('PipelineProgress'));
console.log('在优应的成验术认:?), c.includes('handleRetryAfterReject'));
console.log('在优应的成验术认:?), c.includes('reloadProject'));
console.log('在优应的成验术认:?), c.includes('v-else-if="loadError"'));
if (c.length > o + 800) {
  console.log('✅ 时辺规成功!');
} else {
  console.log('ꠃ缿 指件况应界渹的置件失败 ，请查检查');
}
