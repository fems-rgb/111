<template>
  <div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-surface-800 dark:text-white">🛠️ 技能市场</h1>
      <div class="flex gap-2">
        <button class="btn-secondary text-sm" @click="$router.push('/chat')">💬 在对话中使用 /skill</button>
        <button class="btn-primary text-sm" @click="openPublishDialog">+ 发布自定义 Skill</button>
      </div>
    </div>

    <!-- 联动提示 -->
    <div class="card p-3 border-l-4 border-l-primary-500 flex items-center gap-3 text-sm text-surface-600 dark:text-surface-300">
      <span class="text-lg">💡</span>
      <span>技能可与<strong>资料库</strong>（选择文件作为输入）、<strong>AI对话</strong>（输入 <code class="px-1 py-0.5 bg-surface-100 dark:bg-surface-700 rounded text-xs font-mono">/skill 技能ID input=内容</code>）、<strong>自动化流水线</strong>联动使用</span>
    </div>

    <!-- 加载状态 -->
    <div v-if="loadingSkills" class="card p-8 text-center text-surface-400">
      <span class="inline-block w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mr-2"></span>
      加载技能列表...
    </div>

    <!-- 技能卡片网格 -->
    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div v-for="skill in skills" :key="skill.id"
           class="card p-5 hover:ring-2 ring-primary-300 transition-all cursor-pointer group relative"
           @click="openSkillDialog(skill)">
        <!-- 删除按钮（仅自定义技能） -->
        <button v-if="(skill as any).is_custom" @click.stop="deleteSkill(skill)"
          class="absolute top-2 right-2 w-6 h-6 rounded-full bg-red-100 text-red-500 text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-200">✕</button>
        <div class="text-2xl mb-2">{{ skill.icon }}</div>
        <h3 class="font-semibold text-surface-800 dark:text-white">{{ skill.name }}</h3>
        <p class="text-xs text-surface-500 mt-1 line-clamp-2">{{ skill.description }}</p>
        <div class="mt-3 flex items-center gap-2">
          <span :class="['text-[10px] px-2 py-0.5 rounded-full font-medium',
            (skill as any).type === 'webhook' ? 'bg-purple-100 text-purple-700' :
            (skill as any).is_custom ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700']">
            {{ (skill as any).type === 'webhook' ? '🌐 外接' : (skill as any).is_custom ? '🧠 AI' : '⚙️ 内置' }}
          </span>
          <span class="text-[10px] text-surface-400 group-hover:text-primary-500 transition-colors">点击运行 →</span>
        </div>
      </div>
    </div>

    <!-- ====== 技能执行弹窗 ====== -->
    <Teleport to="body">
      <div v-if="activeSkill" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="activeSkill = null">
        <div class="bg-white dark:bg-surface-800 rounded-2xl shadow-2xl w-[640px] max-h-[85vh] flex flex-col overflow-hidden">
          <div class="flex items-center justify-between px-6 py-4 border-b border-surface-200 dark:border-surface-600">
            <div class="flex items-center gap-2">
              <span class="text-2xl">{{ activeSkill.icon }}</span>
              <div>
                <h3 class="font-semibold text-lg text-surface-800 dark:text-white">{{ activeSkill.name }}</h3>
                <p class="text-xs text-surface-400">{{ activeSkill.description }}</p>
              </div>
            </div>
            <button class="text-surface-400 hover:text-surface-700 text-xl" @click="activeSkill = null">&times;</button>
          </div>

          <div class="flex-1 overflow-auto p-6 space-y-4">
            <!-- 内置: 文献摘要 -->
            <div v-if="activeSkill.id === 'literature_summary'" class="space-y-3">
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300">📚 选择资料库文件</label>
              <select v-model="skillInput.file_id" class="input-field">
                <option value="">-- 请选择文件 --</option>
                <option v-for="doc in knowledgeDocs" :key="doc.id" :value="doc.id">
                  📄 {{ doc.title }} ({{ doc.doc_type }})
                </option>
              </select>
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mt-2">💬 追问（可选，基于摘要提问）</label>
              <input v-model="skillInput.question" class="input-field" placeholder="例如：这篇论文的核心方法是什么？" />
            </div>

            <!-- 内置: 数据清洗 -->
            <div v-else-if="activeSkill.id === 'data_cleaning'" class="space-y-3">
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300">📚 选择资料库数据文件</label>
              <select v-model="skillInput.file_id" class="input-field">
                <option value="">-- 请选择文件 --</option>
                <option v-for="doc in knowledgeDocs" :key="doc.id" :value="(doc as any).saved_name || doc.id">
                  📄 {{ doc.title }}
                </option>
              </select>
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mt-2">🔧 清洗方法</label>
              <select v-model="skillInput.method" class="input-field">
                <option value="zscore">Z-Score 异常值检测</option>
                <option value="iqr">IQR 四分位距法</option>
                <option value="manual">手动阈值</option>
              </select>
            </div>

            <!-- 内置: 代码复现 -->
            <div v-else-if="activeSkill.id === 'code_reproduce'" class="space-y-3">
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300">🔗 GitHub 仓库地址</label>
              <input v-model="skillInput.repo_url" class="input-field" placeholder="https://github.com/user/repo" />
            </div>

            <!-- 自定义技能: 通用输入 + 资料库联动 -->
            <div v-else-if="(activeSkill as any).is_custom" class="space-y-3">
              <!-- 资料库文件选择（联动） -->
              <div v-if="knowledgeDocs.length > 0" class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <label class="block text-sm font-medium text-blue-700 dark:text-blue-300 mb-1">📚 关联资料库文件（可选，文件摘要会注入到 Prompt 中）</label>
                <select v-model="skillInput.file_id" class="input-field text-sm">
                  <option value="">-- 不关联文件 --</option>
                  <option v-for="doc in knowledgeDocs" :key="doc.id" :value="doc.id">
                    📄 {{ doc.title }} ({{ doc.doc_type }})
                  </option>
                </select>
              </div>

              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300">✏️ 输入内容</label>
              <textarea v-model="skillInput.input" rows="4" class="input-field font-mono text-sm"
                placeholder="输入你的问题或指令...&#10;模板中的 {{input}} 会被替换为此内容&#10;如果选了文件，{{file_content}} 会被替换为文件摘要"></textarea>

              <!-- Prompt 模板预览 -->
              <details class="text-xs">
                <summary class="cursor-pointer text-surface-400 hover:text-surface-600">👁️ 查看 Prompt 模板</summary>
                <pre class="mt-2 p-2 bg-surface-50 dark:bg-surface-700 rounded text-surface-600 dark:text-surface-300 whitespace-pre-wrap font-mono text-[11px] max-h-32 overflow-auto">{{ (activeSkill as any).prompt_template || '(无模板)' }}</pre>
              </details>
            </div>

            <!-- 执行结果 -->
            <div v-if="skillResult" class="mt-4 rounded-lg border overflow-hidden"
                 :class="skillResult.status === 'success' ? 'border-green-200 bg-green-50 dark:bg-green-900/20 dark:border-green-800' : 'border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800'">
              <div class="px-4 py-2 flex items-center justify-between"
                   :class="skillResult.status === 'success' ? 'bg-green-100 dark:bg-green-900/40' : 'bg-red-100 dark:bg-red-900/40'">
                <span :class="skillResult.status === 'success' ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'" class="font-medium text-sm">
                  {{ skillResult.status === 'success' ? '✅ 执行成功' : '❌ 执行失败' }}
                </span>
                <span v-if="skillResult.result?.model" class="text-[10px] text-surface-500">
                  {{ skillResult.result.model }} · {{ (skillResult.result.tokens?.input || 0) + (skillResult.result.tokens?.output || 0) }} tokens · ¥{{ (skillResult.result.cost || 0).toFixed(4) }}
                </span>
              </div>
              <div class="p-4">
                <!-- 优先显示 output/summary/message，否则 JSON -->
                <pre v-if="skillResult.result?.output || skillResult.result?.summary || skillResult.result?.message"
                  class="text-sm text-surface-700 dark:text-surface-200 whitespace-pre-wrap font-sans leading-relaxed max-h-60 overflow-auto">{{ skillResult.result.output || skillResult.result.summary || skillResult.result.message }}</pre>
                <pre v-else class="text-xs text-surface-700 dark:text-surface-200 whitespace-pre-wrap font-mono max-h-60 overflow-auto">{{ JSON.stringify(skillResult.result, null, 2) }}</pre>

                <!-- 联动信息 -->
                <div v-if="skillResult.result?.linked_file || skillResult.result?.linked_project" class="mt-3 pt-2 border-t border-surface-200 dark:border-surface-600 text-[11px] text-surface-400 space-y-1">
                  <p v-if="skillResult.result.linked_file">📚 联动文件: {{ skillResult.result.linked_file }}</p>
                  <p v-if="skillResult.result.linked_project">📋 联动项目: {{ skillResult.result.linked_project }}</p>
                </div>
              </div>
            </div>

            <!-- 执行中 loading -->
            <div v-if="running" class="flex items-center gap-2 text-sm text-primary-600">
              <span class="inline-block w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></span>
              AI 正在执行技能...
            </div>
          </div>

          <div class="px-6 py-4 border-t border-surface-200 dark:border-surface-600 flex justify-end gap-3">
            <button @click="activeSkill = null" class="btn-secondary">取消</button>
            <button @click="executeSkill" :disabled="running" class="btn-primary flex items-center gap-2">
              <span v-if="running" class="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              {{ running ? '执行中...' : '▶ 运行' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ====== 发布自定义Skill弹窗 ====== -->
    <Teleport to="body">
      <div v-if="showPublishDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showPublishDialog = false">
        <div class="bg-white dark:bg-surface-800 rounded-2xl shadow-2xl w-full max-w-lg mx-4 p-6 space-y-4 max-h-[90vh] overflow-auto">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-bold text-surface-900 dark:text-white">🛠️ 发布自定义 Skill</h3>
            <button @click="showPublishDialog = false" class="text-surface-400 hover:text-surface-600 text-xl">✕</button>
          </div>

          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">技能名称</label>
              <input v-model="publishForm.name" type="text" placeholder="例如：论文润色助手"
                class="w-full px-3 py-2 border border-surface-200 dark:border-surface-600 rounded-lg bg-white dark:bg-surface-700 text-surface-900 dark:text-white focus:ring-2 focus:ring-primary-500 outline-none" />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">描述</label>
              <textarea v-model="publishForm.description" rows="2" placeholder="简要描述技能功能..."
                class="w-full px-3 py-2 border border-surface-200 dark:border-surface-600 rounded-lg bg-white dark:bg-surface-700 text-surface-900 dark:text-white focus:ring-2 focus:ring-primary-500 outline-none resize-none" />
            </div>

            <!-- 技能类型切换 -->
            <div class="flex gap-2">
              <button @click="publishMode = 'prompt'" :class="['flex-1 py-2 rounded-lg text-sm font-medium transition', publishMode === 'prompt' ? 'bg-primary-600 text-white' : 'bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-300']">
                🧠 Prompt 技能
              </button>
              <button @click="publishMode = 'webhook'" :class="['flex-1 py-2 rounded-lg text-sm font-medium transition', publishMode === 'webhook' ? 'bg-purple-600 text-white' : 'bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-300']">
                🌐 外接 Webhook
              </button>
            </div>

            <div v-if="publishMode === 'prompt'">
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Prompt 模板</label>
              <textarea v-model="publishForm.prompt_template" rows="5"
                placeholder="输入 Prompt 模板，可用占位符:&#10;{{input}} - 用户输入&#10;{{file_content}} - 资料库文件摘要&#10;{{project_context}} - 项目上下文"
                class="w-full px-3 py-2 border border-surface-200 dark:border-surface-600 rounded-lg bg-white dark:bg-surface-700 text-surface-900 dark:text-white font-mono text-sm focus:ring-2 focus:ring-primary-500 outline-none resize-none" />
              <p class="text-[11px] text-surface-400 mt-1">💡 支持的占位符: <code v-pre>{{input}}</code> <code v-pre>{{file_content}}</code> <code v-pre>{{project_context}}</code> 或任意 <code v-pre>{{key}}</code></p>
            </div>

            <div v-else class="space-y-2">
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Webhook URL</label>
              <input v-model="publishForm.webhook_url" type="text" placeholder="https://your-api.com/skill/run"
                class="w-full px-3 py-2 border border-surface-200 dark:border-surface-600 rounded-lg bg-white dark:bg-surface-700 text-surface-900 dark:text-white focus:ring-2 focus:ring-purple-500 outline-none text-sm" />
              <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">HTTP 方法</label>
              <select v-model="publishForm.webhook_method" class="input-field text-sm">
                <option value="POST">POST</option>
                <option value="GET">GET</option>
              </select>
            </div>

            <div class="flex gap-3">
              <div>
                <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">图标</label>
                <input v-model="publishForm.icon" type="text" placeholder="🔬" maxlength="4"
                  class="w-16 px-2 py-2 border border-surface-200 dark:border-surface-600 rounded-lg bg-white dark:bg-surface-700 text-center text-xl" />
              </div>
              <div class="flex-1">
                <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">可见性</label>
                <select v-model="publishForm.is_public" class="input-field text-sm">
                  <option :value="true">🌐 公开（所有人可用）</option>
                  <option :value="false">🔒 私有（仅自己可用）</option>
                </select>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button @click="showPublishDialog = false" class="px-4 py-2 text-sm text-surface-600 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg transition">取消</button>
            <button @click="handlePublishSkill"
              :disabled="!publishForm.name || (publishMode === 'prompt' && !publishForm.prompt_template) || (publishMode === 'webhook' && !publishForm.webhook_url) || publishing"
              class="px-4 py-2 text-sm bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed">
              {{ publishing ? '发布中...' : '🚀 发布' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { skillsApi, type SkillInfo } from '@/api/modules/skills'
import { useAppStore } from '@/stores/app'
import { knowledgeApi, type KnowledgeDoc } from '@/api/modules/knowledge'

const appStore = useAppStore()

const skills = ref<SkillInfo[]>([])
const loadingSkills = ref(false)
const activeSkill = ref<SkillInfo | null>(null)
const skillInput = ref<Record<string, any>>({})
const skillResult = ref<any>(null)
const running = ref(false)
const knowledgeDocs = ref<KnowledgeDoc[]>([])

// 发布表单
const showPublishDialog = ref(false)
const publishing = ref(false)
const publishMode = ref<'prompt' | 'webhook'>('prompt')
const publishForm = reactive({
  name: '',
  description: '',
  prompt_template: '',
  icon: '🔧',
  is_public: true,
  webhook_url: '',
  webhook_method: 'POST',
})

function openPublishDialog() {
  publishForm.name = ''
  publishForm.description = ''
  publishForm.prompt_template = ''
  publishForm.icon = '🔧'
  publishForm.is_public = true
  publishForm.webhook_url = ''
  publishForm.webhook_method = 'POST'
  publishMode.value = 'prompt'
  showPublishDialog.value = true
}

async function handlePublishSkill() {
  if (!publishForm.name) return
  if (publishMode.value === 'prompt' && !publishForm.prompt_template) return
  if (publishMode.value === 'webhook' && !publishForm.webhook_url) return

  publishing.value = true
  try {
    await skillsApi.create({
      name: publishForm.name,
      description: publishForm.description,
      prompt_template: publishMode.value === 'prompt' ? publishForm.prompt_template : '',
      icon: publishForm.icon,
      category: 'custom',
      is_public: publishForm.is_public,
      webhook_url: publishMode.value === 'webhook' ? publishForm.webhook_url : '',
      webhook_method: publishForm.webhook_method,
    })
    showPublishDialog.value = false
    appStore.showToast('✅ 技能已发布', 'success')
    await loadSkills()
  } catch (e: any) {
    appStore.showToast('发布失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    publishing.value = false
  }
}

async function loadSkills() {
  loadingSkills.value = true
  try {
    const res = await skillsApi.list()
    skills.value = res.data.skills || []
  } catch (e: any) {
    appStore.showToast('加载技能列表失败', 'error')
  } finally {
    loadingSkills.value = false
  }
}

onMounted(async () => {
  await loadSkills()
  try {
    const docsRes = await knowledgeApi.listDocs({ limit: 200 })
    knowledgeDocs.value = docsRes.data as any
  } catch {}
})

function openSkillDialog(skill: SkillInfo) {
  activeSkill.value = skill
  skillInput.value = {}
  skillResult.value = null
}

async function executeSkill() {
  if (!activeSkill.value) return
  running.value = true
  skillResult.value = null
  try {
    const res = await skillsApi.run(activeSkill.value.id, skillInput.value)
    skillResult.value = res.data
    appStore.showToast('✅ ' + activeSkill.value.name + ' 执行完成', 'success')
  } catch (e: any) {
    skillResult.value = { status: 'error', result: { message: e.response?.data?.detail || e.message } }
    appStore.showToast('执行失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    running.value = false
  }
}

async function deleteSkill(skill: SkillInfo) {
  if (!confirm(`确定删除技能「${skill.name}」？`)) return
  try {
    await skillsApi.delete(skill.id)
    appStore.showToast('🗑️ 技能已删除', 'success')
    await loadSkills()
  } catch (e: any) {
    appStore.showToast('删除失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}
</script>