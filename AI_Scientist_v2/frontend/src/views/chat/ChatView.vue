<template>
  <div class="chat-layout">
    <div class="chat-main">
      <div class="chat-topbar"><span class="topbar-title">💬 AI 学术助手</span><div class="topbar-actions"><button class="topbar-btn" @click="startNewChat" title="开始新对话">✨ 新对话</button><button class="topbar-btn" @click="loadHistory" title="加载历史记录">📜 历史</button><button class="topbar-btn danger" @click="clearAll" title="清除所有对话">🗑️ 清除</button></div></div>
      <div class="chat-messages" ref="msgBox">
        <div v-for="m in messages" :key="m.id" :class="['msg',m.role]"><div class="msg-bubble" v-html="formatContent(m.content)"></div></div>
        <div v-if="streaming" class="msg assistant"><div class="msg-bubble typing">⏳ 思考中...</div></div>
      </div>
      <div class="chat-input-area">
        <ChatToolbar :project-id="projectId" :steps="currentSteps" @files="handleFiles" @kb-search="triggerKbSearch" @pipeline-saved="onPipelineSaved" @feedback-submitted="onFeedbackSubmitted" />
        <div class="input-row">
          <textarea v-model="inputText" @keydown.enter.exact.prevent="send" placeholder="输入研究问题或指令... (输入 /help 查看命令)" rows="1" />
          <button class="send-btn" @click="send" :disabled="!inputText.trim()||streaming">发送</button>
        </div>
      </div>
    </div>
    <HypothesisPanel v-if="showHypoPanel" :project-id="projectId" ref="hypoPanelRef" @feedback="onHypoFeedback" />
    <button class="toggle-hypo" @click="showHypoPanel=!showHypoPanel" :title="showHypoPanel?'收起假设面板':'展开假设面板'">{{ showHypoPanel?'▶':'💡' }}</button>

    <!-- 赛道一增量：人工反馈对话框 -->
    <Teleport to="body">
      <div v-if="feedbackDialog.visible" class="fb-overlay" @click.self="feedbackDialog.visible=false">
        <div class="fb-dialog">
          <h3 class="fb-title">{{ feedbackDialog.action === 'accept' ? '✅ 采纳假设' : feedbackDialog.action === 'reject' ? '❌ 拒绝假设' : '✏️ 修改假设' }}</h3>
          <p class="fb-hypo-id">{{ feedbackDialog.hypoId }}</p>
          <textarea v-model="feedbackDialog.comment" class="fb-textarea" placeholder="请输入反馈意见（可选）..." rows="3"></textarea>
          <div class="fb-actions">
            <button class="fb-cancel" @click="feedbackDialog.visible=false">取消</button>
            <button class="fb-confirm" :class="'fb-'+feedbackDialog.action" @click="submitFeedback">确认提交</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ChatToolbar from '@/components/chat/ChatToolbar.vue'
import HypothesisPanel from '@/components/hypothesis/HypothesisPanel.vue'
import { chatApi } from '@/api/modules/chat'
import { knowledgeApi } from '@/api/modules/knowledge'

const route = useRoute()
const projectId = computed(()=>Number(route.params.projectId||route.query.projectId||0))

interface Msg{id:number;role:'user'|'assistant';content:string}
const messages = ref<Msg[]>([])
const inputText = ref('')
const streaming = ref(false)
const showHypoPanel = ref(false)
const currentSteps = ref<string[]>([])
const msgBox = ref<HTMLElement>()
const hypoPanelRef = ref<InstanceType<typeof HypothesisPanel>>()
let msgIdCounter = 0

function pushMsg(role:'user'|'assistant', content:string){
  messages.value.push({id:++msgIdCounter, role, content})
  nextTick(scrollToBottom)
}

// ===== 斜杠命令拦截 =====
async function handleSlashCommand(cmd: string): Promise<boolean> {
  const command = cmd.trim().toLowerCase()

  if (command === '/help') {
    pushMsg('assistant',
      '📋 **可用命令：**\n\n' +
      '• `/help` — 显示帮助信息\n' +
      '• `/history` — 重新加载对话历史\n' +
      '• `/delete` — 清除所有对话历史\n' +
      '• `/clear` — 仅清空当前屏幕（不删服务端记录）\n' +
      '• `/skill` — 在对话中调用技能市场\n\n' +
      '直接输入文字即可与AI助手对话。'
    )
    return true
  }

  if (command === '/clear') {
    messages.value = []
    msgIdCounter = 0
    pushMsg('assistant', '🧹 已清空当前屏幕。服务端历史记录仍保留，输入 `/history` 可重新加载。')
    return true
  }

  if (command === '/delete') {
    try {
      const pid = projectId.value || undefined
      await chatApi.deleteHistory(pid)
      messages.value = []
      msgIdCounter = 0
      pushMsg('assistant', '🗑️ 已清除所有对话历史（服务端已删除）。')
    } catch(e:any) {
      pushMsg('assistant', `⚠️ 删除失败: ${e?.response?.data?.detail || e?.message || '未知错误'}`)
    }
    return true
  }

  if (command === '/history') {
    await loadHistory()
    pushMsg('assistant', `📜 已重新加载 ${messages.value.length} 条历史消息。`)
    return true
  }

  if (command.startsWith('/skill')) {
    // /skill 命令发给后端处理
    return false
  }

  // 未知命令也发给后端
  return false
}

// ===== 发送消息 =====
async function send(){
  const text = inputText.value.trim()
  if(!text || streaming.value) return
  inputText.value = ''

  // 斜杠命令拦截
  if (text.startsWith('/')) {
    const handled = await handleSlashCommand(text)
    if (handled) return
  }

  pushMsg('user', text)
  streaming.value = true
  await nextTick(); scrollToBottom()

  try {
    const res = await chatApi.send(text, projectId.value || undefined)
    const data = res.data
    pushMsg('assistant', data.reply || '[无回复内容]')
  } catch(e:any) {
    const errMsg = e?.response?.data?.detail || e?.message || '未知错误'
    pushMsg('assistant', `⚠️ 请求失败: ${errMsg}`)
  } finally {
    streaming.value = false
    scrollToBottom()
    hypoPanelRef.value?.refresh()
  }
}

// ===== 加载历史 =====
async function loadHistory(){
  try {
    const pid = projectId.value || undefined
    const res = await chatApi.history(pid, 50)
    const list = res.data || []
    messages.value = list.map((m:any, i:number) => ({id: i+1, role: m.role, content: m.content}))
    msgIdCounter = messages.value.length
    scrollToBottom()
  } catch(e){ console.error('加载历史失败', e) }
}

// ===== Markdown简易格式化 =====
function formatContent(text: string): string {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code style="background:#f0f0f0;padding:1px 4px;border-radius:3px;font-size:13px">$1</code>')
    .replace(/\n/g, '<br>')
  return html
}

function handleFiles(files:File[]){pushMsg('user', `📎 已上传 ${files.length} 个文件：${files.map(f=>f.name).join(', ')}`)}
async function triggerKbSearch(){
  const query = inputText.value.trim() || prompt('请输入知识库检索关键词：')
  if(!query) return
  pushMsg('user', `🔍 知识库检索: ${query}`)
  streaming.value = true
  await nextTick(); scrollToBottom()
  try {
    const res = await knowledgeApi.searchKnowledge({ q: query, limit: 8 })
    const data = res.data
    const items = data.results || []
    if(items.length === 0){
      pushMsg('assistant', `📭 未在知识库中找到与「${query}」相关的文档。\n\n💡 建议：\n• 尝试其他关键词\n• 先上传相关文献到知识库\n• 使用外部学术搜索导入资料`)
    } else {
      let reply = `📚 **知识库检索结果** (${data.total}条)\n\n`
      items.forEach((item: any, idx: number) => {
        reply += `**${idx+1}. ${item.filename}** [${item.file_ext}]\n`
        if(item.summary) reply += `> ${item.summary.slice(0,150)}...\n`
        if(item.tags?.length) reply += `🏷️ ${item.tags.join(', ')}\n`
        reply += '\n'
      })
      reply += `💡 输入文档编号可查看详情，或继续提问让AI结合知识库回答。`
      pushMsg('assistant', reply)
    }
  } catch(e: any){
    pushMsg('assistant', `⚠️ 知识库检索失败: ${e?.response?.data?.detail || e?.message || '未知错误'}`)
  } finally {
    streaming.value = false
    scrollToBottom()
  }
}
function onPipelineSaved(steps:string[]){currentSteps.value=steps;pushMsg('assistant', `⚙️ 流水线已更新：${steps.join(' → ')}`)}
function onFeedbackSubmitted(){pushMsg('assistant', '🔄 反馈已提交，新一轮迭代已触发');hypoPanelRef.value?.refresh()}
function scrollToBottom(){nextTick(()=>{if(msgBox.value)msgBox.value.scrollTop=msgBox.value.scrollHeight})}

async function clearAll(){
  if(!confirm('确定清除所有对话历史？此操作不可撤销。')) return
  try {
    const pid = projectId.value || undefined
    await chatApi.deleteHistory(pid)
    messages.value = []
    msgIdCounter = 0
    pushMsg('assistant', '🗑️ 已清除所有对话历史。')
  } catch(e:any) {
    pushMsg('assistant', `⚠️ 清除失败: ${e?.response?.data?.detail || e?.message}`)
  }
}
function startNewChat(){
  messages.value = []
  msgIdCounter = 0
  pushMsg('assistant', '👋 新对话已开始，输入研究问题即可对话（/help 查看命令，📜 可加载历史记录）。')
}
// ===== 赛道一增量：人工反馈交互 =====
const feedbackDialog = ref({ visible: false, hypoId: '', action: '' as 'accept'|'reject'|'revise', comment: '' })

function onHypoFeedback(hypoId: string, action: 'accept'|'reject'|'revise') {
  feedbackDialog.value = { visible: true, hypoId, action, comment: '' }
}

async function submitFeedback() {
  const { hypoId, action, comment } = feedbackDialog.value
  if (!projectId.value) return
  try {
    await chatApi.send(`[FEEDBACK] ${action.toUpperCase()} ${hypoId}: ${comment}`, projectId.value)
    pushMsg('assistant', `🔄 已${action === 'accept' ? '采纳' : action === 'reject' ? '拒绝' : '修改'}假设 ${hypoId}，新一轮迭代已触发`)
    hypoPanelRef.value?.refresh()
  } catch (e: any) {
    pushMsg('assistant', `⚠️ 反馈提交失败: ${e?.response?.data?.detail || e?.message}`)
  } finally {
    feedbackDialog.value.visible = false
  }
}

onMounted(()=>{ pushMsg('assistant', '👋 新对话已开始，输入研究问题即可对话（/help 查看命令，📜 可加载历史记录）。'); scrollToBottom() })
</script>

<style scoped>
.chat-layout{display:flex;height:100vh;position:relative}
.chat-main{flex:1;display:flex;flex-direction:column;min-width:0}
.chat-messages{flex:1;overflow-y:auto;padding:16px}
.msg{margin-bottom:12px;display:flex}
.msg.user{justify-content:flex-end}
.msg-bubble{max-width:72%;padding:10px 14px;border-radius:12px;font-size:14px;line-height:1.6;word-break:break-word}
.msg.user .msg-bubble{background:#1a73e8;color:#fff;border-bottom-right-radius:4px}
.msg.assistant .msg-bubble{background:#f0f2f5;color:#333;border-bottom-left-radius:4px}
.msg.assistant .msg-bubble :deep(strong){font-weight:600}
.msg.assistant .msg-bubble :deep(code){font-family:monospace}
.typing{opacity:.7}
.chat-input-area{border-top:1px solid #e5e7eb;background:#fff}
.input-row{display:flex;gap:8px;padding:10px;align-items:flex-end}
.input-row textarea{flex:1;resize:none;border:1px solid #ddd;border-radius:8px;padding:10px;font-size:14px;font-family:inherit;max-height:120px}
.send-btn{padding:10px 20px;background:#1a73e8;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;white-space:nowrap}
.send-btn:disabled{opacity:.5;cursor:not-allowed}
.toggle-hypo{position:absolute;right:0;top:50%;transform:translateY(-50%);z-index:50;background:#fff;border:1px solid #e5e7eb;border-right:none;border-radius:8px 0 0 8px;padding:12px 6px;cursor:pointer;font-size:16px}
.fb-overlay{position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:999;display:flex;align-items:center;justify-content:center}
.fb-dialog{background:#fff;border-radius:12px;padding:24px;width:420px;max-width:90vw;box-shadow:0 20px 60px rgba(0,0,0,.2)}
.fb-title{font-size:16px;font-weight:700;margin-bottom:8px}
.fb-hypo-id{font-size:13px;color:#1a73e8;margin-bottom:12px;font-weight:600}
.fb-textarea{width:100%;border:1px solid #ddd;border-radius:8px;padding:10px;font-size:14px;resize:vertical;margin-bottom:12px;font-family:inherit}
.fb-actions{display:flex;gap:8px;justify-content:flex-end}
.fb-cancel{padding:8px 16px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer;font-size:13px}
.fb-confirm{padding:8px 16px;border:none;border-radius:6px;color:#fff;cursor:pointer;font-size:13px;font-weight:600}
.fb-accept{background:#28a745}.fb-reject{background:#dc3545}.fb-revise{background:#ffc107;color:#333}
.chat-topbar{display:flex;align-items:center;justify-content:space-between;padding:8px 16px;border-bottom:1px solid #e5e7eb;background:#fafbfc}
.topbar-title{font-size:14px;font-weight:600;color:#333}
.topbar-actions{display:flex;gap:6px}
.topbar-btn{padding:4px 10px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer;font-size:12px;transition:all .2s}
.topbar-btn:hover{background:#f0f2f5;border-color:#bbb}
.topbar-btn.danger:hover{background:#fee;border-color:#f99;color:#c00}
.hypo-panel{width:320px;min-width:280px;border-left:1px solid #e5e7eb;overflow-y:auto;background:#fafbfc}
</style>


