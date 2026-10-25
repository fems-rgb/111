<template>
  <Teleport to="body">
    <div v-if="visible" class="cmd-overlay" @click.self="close">
      <div class="cmd-box">
        <div class="cmd-input-row">
          <span class="cmd-icon">🔍</span>
          <input ref="inputRef" v-model="query" placeholder="搜索页面、项目、题目、技能、流水线、知识文件…  (↑↓ 选择 · Enter 跳转 · Esc 关闭)"
                 class="cmd-input" @keydown.down.prevent="moveDown" @keydown.up.prevent="moveUp"
                 @keydown.enter.prevent="selectCurrent" @keydown.esc.prevent="close" />
          <span class="cmd-hint">⌘K</span>
        </div>
        <div class="cmd-list">
          <div v-if="loading" class="cmd-empty">⏳ 加载索引中...</div>
          <div v-else-if="filteredList.length===0" class="cmd-empty">无匹配结果</div>
          <template v-else>
            <div v-for="(group, gname) in grouped" :key="gname" class="cmd-group">
              <div class="cmd-group-title">{{ gname }}</div>
              <div v-for="item in group" :key="item._id"
                   :class="['cmd-item', item._idx===activeIdx ? 'cmd-active' : '']"
                   @click="select(item)" @mouseenter="activeIdx = item._idx">
                <span class="cmd-item-icon">{{ item.icon }}</span>
                <div class="cmd-item-body">
                  <div class="cmd-item-title">{{ item.title }}</div>
                  <div v-if="item.subtitle" class="cmd-item-sub">{{ item.subtitle }}</div>
                </div>
                <span v-if="item.badge" class="cmd-item-badge">{{ item.badge }}</span>
              </div>
            </div>
          </template>
        </div>
        <div class="cmd-footer">
          <span>💡 试试: <code>做 PPT</code> · <code>项目</code> · <code>题库</code> · <code>技能</code> · <code>流水线</code></span>
          <span class="cmd-footer-right">共 {{ filteredList.length }} 项</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useProjectStore } from '@/stores/project'
import { useAppStore } from '@/stores/app'
import { getQuestions } from '@/api/modules/questions'
import { automationApi } from '@/api/modules/automation'
import { knowledgeApi } from '@/api/modules/knowledge'
import { courseApi, type Course } from '@/api/modules/courses'

interface CmdItem { _id: string; _idx: number; icon: string; title: string; subtitle?: string; badge?: string; group: string; action: () => void }

const router = useRouter()
const projectStore = useProjectStore()
const appStore = useAppStore()
const { projects } = storeToRefs(projectStore)

const visible = ref(false)
const query = ref('')
const inputRef = ref<HTMLInputElement>()
const activeIdx = ref(0)
const loading = ref(false)

// 缓存索引数据
const questionsCache = ref<any[]>([])
const pipelinesCache = ref<any[]>([])
const knowledgeCache = ref<any[]>([])
const coursesCache = ref<Course[]>([])

const PAGES: Array<{ icon: string; title: string; subtitle: string; path: string; keywords: string }> = [
  { icon: '🏠', title: '首页 Dashboard', subtitle: '项目 & 概览', path: '/', keywords: 'home dashboard 首页' },
  { icon: '💬', title: 'AI 对话', subtitle: '与学术助手对话', path: '/chat', keywords: 'chat ai 对话' },
  { icon: '📚', title: '科学问题题库', subtitle: 'Science 125 · 生成研究方案', path: '/questions', keywords: 'question science 题库' },
  { icon: '🎓', title: '课程中心', subtitle: '开课 / 选课 / PPT 电子化阅读 / AI 更新课件', path: '/courses', keywords: 'course teaching 课程 课件 上课' },
  { icon: '📽️', title: 'AI 生成 PPT 课件', subtitle: '课件工坊 · 一个主题直接出整套课件并下载 .pptx', path: '/courseware-studio', keywords: 'ppt powerpoint slide 课件 生成 工坊 做ppt studio deck' },
  { icon: '🗂️', title: '资料库', subtitle: '本地文件 + 外部学术搜索', path: '/knowledge', keywords: 'knowledge 资料库 文献' },
  { icon: '🛠️', title: '技能市场', subtitle: '内置/自定义/webhook 技能', path: '/skills', keywords: 'skill market 技能' },
  { icon: '⚙️', title: '自动化流水线', subtitle: '多 Agent 编排 · 定时 · 反馈迭代', path: '/automation', keywords: 'pipeline automation 流水线' },
  { icon: '🧪', title: '实验模拟场', subtitle: '假设验证 · 数据分析', path: '/experiment-lab', keywords: 'experiment lab 实验' },
  { icon: '🤖', title: 'Agent 中心', subtitle: '单 Agent Playground', path: '/agents', keywords: 'agent playground' },
  { icon: '📊', title: 'Trace 观测', subtitle: '链路追踪', path: '/traces', keywords: 'trace observability' },
  { icon: '💰', title: '成本观测', subtitle: 'Token 消费统计', path: '/cost', keywords: 'cost token' },
  { icon: '⚙️', title: '设置', subtitle: 'API Key & 模型配置', path: '/settings', keywords: 'settings 设置' },
  { icon: '🛡️', title: '管理后台', subtitle: '用户与系统管理', path: '/admin', keywords: 'admin 管理员' },
]

async function loadIndexes() {
  // 确保项目列表已加载
  if (!(projects.value && projects.value.length)) {
    try { await projectStore.fetchProjects() } catch { /* ignore */ }
  }
  if (questionsCache.value.length && pipelinesCache.value.length && knowledgeCache.value.length && coursesCache.value.length) return
  loading.value = true
  try {
    const [qRes, pRes, kRes, cRes] = await Promise.allSettled([
      getQuestions({ page_size: 50 } as any),
      automationApi.list(),
      knowledgeApi.listDocs({ limit: 50 }),
      courseApi.list({ scope: 'all', limit: 50 }),
    ])
    if (qRes.status === 'fulfilled') {
      const raw: any = (qRes.value as any).data
      questionsCache.value = raw?.items || raw?.questions || []
    }
    if (pRes.status === 'fulfilled') pipelinesCache.value = (pRes.value as any).data?.pipelines || []
    if (kRes.status === 'fulfilled') {
      const raw: any = (kRes.value as any).data
      knowledgeCache.value = Array.isArray(raw) ? raw : (raw?.items || [])
    }
    if (cRes.status === 'fulfilled') coursesCache.value = (cRes.value as any).data?.items || []
  } finally { loading.value = false }
}

const allItems = computed<CmdItem[]>(() => {
  const items: CmdItem[] = []
  let idx = 0
  // Pages
  for (const p of PAGES) {
    if (appStore.currentWorkspace !== 'personal' && p.path === '/admin') continue
    items.push({ _id: `pg-${p.path}`, _idx: idx++, icon: p.icon, title: p.title, subtitle: p.subtitle, group: '📄 页面', action: () => router.push(p.path) })
  }
  // Projects
  for (const prj of projects.value as any[]) {
    items.push({ _id: `pj-${prj.id}`, _idx: idx++, icon: '📁', title: prj.title || `项目 #${prj.id}`, subtitle: prj.research_question?.slice(0, 60) || prj.domain || '', group: '📁 我的项目', badge: prj.status, action: () => router.push(`/project/${prj.id}`) })
  }
  // Questions
  for (const q of questionsCache.value) {
    items.push({ _id: `qs-${q.question_id}`, _idx: idx++, icon: '❓', title: `#${q.question_id} ${q.title || ''}`, subtitle: [q.category, q.difficulty].filter(Boolean).join(' · '), group: '📚 科学问题题库', action: () => router.push(`/questions?highlight=${q.question_id}`) })
  }
  // Pipelines
  for (const pl of pipelinesCache.value) {
    items.push({ _id: `pl-${pl.id}`, _idx: idx++, icon: '⚙️', title: pl.name, subtitle: `${pl.steps?.length || 0} 步 · ${pl.trigger}`, group: '🔧 自动化流水线', badge: pl.status, action: () => router.push(`/automation?pipeline=${pl.id}`) })
  }
  // Knowledge files
  for (const f of knowledgeCache.value.slice(0, 30)) {
    items.push({ _id: `kb-${f.id || f.file_id || f.title}`, _idx: idx++, icon: '📄', title: f.title || f.filename || '未命名', subtitle: `${(f.doc_type||'').toUpperCase()} · ${f.status || ''}`, group: '🗂️ 资料库文件', action: () => router.push(`/chat?attachments=${encodeURIComponent(String(f.id || f.file_id || ''))}&prefill=${encodeURIComponent('请基于这份资料回答我的问题')}`) })
  }
  // Courses
  for (const c of coursesCache.value) {
    items.push({ _id: `cs-${c.id}`, _idx: idx++, icon: c.cover_emoji || '🎓', title: c.title,
      subtitle: `${c.teacher_name || ''}${c.domain ? ' · ' + c.domain : ''} · ${c.courseware_count} 件课件`,
      group: '🎓 课程', badge: c.is_enrolled ? '已选' : undefined,
      action: () => router.push(`/course/${c.id}`) })
    for (const w of (c.coursewares || []).filter(x => x.status === 'ready').slice(0, 3)) {
      items.push({ _id: `cw-${w.id}`, _idx: idx++, icon: w.source_type === 'ai_generated' ? '🤖' : '📊',
        title: `${c.title} › ${w.title}`, subtitle: `${w.slide_count} 页 · v${w.version}`, group: '📖 课件',
        action: () => router.push(`/course/${c.id}/read/${w.id}`) })
    }
  }
  return items
})

const filteredList = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return allItems.value.slice(0, 30)
  const score = (it: CmdItem) => {
    const hay = (it.title + ' ' + (it.subtitle || '') + ' ' + it.group).toLowerCase()
    if (hay.startsWith(q)) return 3
    if (hay.includes(q)) return 2
    // 分词匹配
    const tokens = q.split(/\s+/).filter(Boolean)
    return tokens.every(t => hay.includes(t)) ? 1 : 0
  }
  return allItems.value.map(it => ({ it, s: score(it) })).filter(x => x.s > 0)
    .sort((a, b) => b.s - a.s).slice(0, 40).map(x => x.it)
})

const grouped = computed(() => {
  const g: Record<string, CmdItem[]> = {}
  for (const it of filteredList.value) {
    ;(g[it.group] ||= []).push(it)
  }
  // 重新分配 _idx
  let idx = 0
  for (const key of Object.keys(g)) {
    g[key] = g[key].map(it => ({ ...it, _idx: idx++ }))
  }
  return g
})

const flatOrdered = computed(() => Object.values(grouped.value).flat())

function moveDown() { activeIdx.value = Math.min(activeIdx.value + 1, flatOrdered.value.length - 1); scrollToActive() }
function moveUp() { activeIdx.value = Math.max(activeIdx.value - 1, 0); scrollToActive() }
function selectCurrent() { const it = flatOrdered.value[activeIdx.value]; if (it) select(it) }
function select(it: CmdItem) { close(); it.action() }
function scrollToActive() {
  nextTick(() => {
    const el = document.querySelector('.cmd-active') as HTMLElement
    if (el) el.scrollIntoView({ block: 'nearest' })
  })
}

function open() {
  visible.value = true
  query.value = ''
  activeIdx.value = 0
  nextTick(() => inputRef.value?.focus())
  loadIndexes()
}
function close() { visible.value = false }

watch(query, () => { activeIdx.value = 0 })

function _keyHandler(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    if (visible.value) close(); else open()
  }
}
onMounted(() => window.addEventListener('keydown', _keyHandler))
onUnmounted(() => window.removeEventListener('keydown', _keyHandler))

defineExpose({ open, close })
</script>

<style scoped>
.cmd-overlay{position:fixed;inset:0;background:rgba(15,23,42,.55);backdrop-filter:blur(3px);z-index:9999;display:flex;justify-content:center;padding-top:12vh}
.cmd-box{background:#fff;border-radius:14px;box-shadow:0 25px 60px rgba(0,0,0,.35);width:640px;max-width:92vw;max-height:72vh;display:flex;flex-direction:column;overflow:hidden;animation:cmd-in .15s ease}
@keyframes cmd-in{from{transform:translateY(-8px);opacity:0}to{transform:translateY(0);opacity:1}}
.cmd-input-row{display:flex;align-items:center;gap:10px;padding:14px 18px;border-bottom:1px solid #eaecef;background:#fafbfc}
.cmd-icon{font-size:16px;color:#64748b}
.cmd-input{flex:1;border:none;background:transparent;outline:none;font-size:14px;color:#0f172a}
.cmd-hint{font-size:11px;color:#94a3b8;padding:2px 8px;background:#f1f5f9;border-radius:4px;font-family:monospace}
.cmd-list{flex:1;overflow-y:auto;padding:6px 0}
.cmd-group-title{padding:8px 18px 4px;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:.5px}
.cmd-item{display:flex;align-items:center;gap:12px;padding:8px 18px;cursor:pointer;transition:background .1s}
.cmd-item:hover,.cmd-active{background:#eff6ff}
.cmd-active{border-left:3px solid #3b82f6;padding-left:15px}
.cmd-item-icon{font-size:16px;flex-shrink:0;width:22px}
.cmd-item-body{flex:1;min-width:0}
.cmd-item-title{font-size:13px;color:#1e293b;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cmd-item-sub{font-size:11px;color:#64748b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:1px}
.cmd-item-badge{font-size:10px;padding:2px 6px;background:#e2e8f0;border-radius:8px;color:#475569;flex-shrink:0}
.cmd-empty{text-align:center;padding:40px;color:#94a3b8;font-size:13px}
.cmd-footer{padding:8px 18px;border-top:1px solid #eaecef;background:#fafbfc;font-size:11px;color:#64748b;display:flex;justify-content:space-between}
.cmd-footer code{background:#e2e8f0;padding:1px 5px;border-radius:3px;margin:0 2px;font-family:monospace}
.cmd-footer-right{color:#94a3b8}
</style>
