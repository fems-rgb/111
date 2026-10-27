<template>
  <div class="space-y-5 animate-fade-in">
    <div v-if="loading" class="card p-8 text-center text-surface-400 text-sm">⏳ 加载课程…</div>

    <template v-else-if="course">
      <!-- ═══ 课程头 ═══ -->
      <div class="card p-6">
        <div class="flex items-start gap-4">
          <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center text-3xl flex-shrink-0">
            {{ course.cover_emoji || '📖' }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <h1 class="text-xl font-bold">{{ course.title }}</h1>
              <span :class="['text-[11px] px-2 py-0.5 rounded-full font-medium',
                             course.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700']">
                {{ course.status === 'published' ? '已发布' : '草稿' }}
              </span>
              <span v-if="course.code" class="text-[11px] px-2 py-0.5 rounded bg-surface-100 font-mono">{{ course.code }}</span>
              <span v-if="course.domain" class="text-[11px] px-2 py-0.5 rounded bg-blue-50 text-blue-700">{{ course.domain }}</span>
            </div>
            <p class="text-sm text-surface-500 mt-1.5">
              {{ course.teacher_name }}{{ course.teacher_institution ? ' · ' + course.teacher_institution : '' }}
              · 🎒 {{ course.enroll_count }} 人选修 · 👀 {{ course.view_count }} 次浏览
            </p>
            <p v-if="course.description" class="text-sm text-surface-600 mt-2">{{ course.description }}</p>
          </div>
          <div class="flex flex-col gap-2 items-end flex-shrink-0">
            <!-- 学生视角 -->
            <button v-if="!isTeacher && course.status === 'published'" @click="toggleEnroll"
                    :class="['px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                             course.is_enrolled ? 'bg-surface-100 text-surface-600 hover:bg-surface-200' : 'bg-primary-600 text-white hover:bg-primary-700']">
              {{ course.is_enrolled ? '✅ 已选修（退课）' : '🎒 选修这门课' }}
            </button>
            <button v-if="isTeacher && course.status !== 'published'" @click="setStatus('published')"
                    class="px-4 py-2 rounded-lg text-sm font-medium bg-green-600 text-white hover:bg-green-700">
              🚀 发布课程
            </button>
            <button v-else-if="isTeacher" @click="setStatus('draft')"
                    class="px-3 py-1.5 rounded-lg text-xs bg-surface-100 hover:bg-surface-200">撤回为草稿</button>
          </div>
        </div>

        <!-- 学习进度（学生） -->
        <div v-if="course.enrollment" class="mt-4 p-3 rounded-lg bg-green-50 border border-green-100">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="font-medium text-green-800">📈 我的学习进度</span>
            <span class="text-green-700">{{ course.enrollment.progress }}%</span>
          </div>
          <div class="h-2 rounded-full bg-green-100 overflow-hidden">
            <div class="h-full bg-green-500 transition-all" :style="{ width: course.enrollment.progress + '%' }"></div>
          </div>
          <button v-if="course.enrollment.last_courseware_id" @click="openReader(course.enrollment.last_courseware_id)"
                  class="mt-2 text-xs text-green-700 hover:underline">
          ▶ 继续上次学习（课件 #{{ course.enrollment.last_courseware_id }} · 第 {{ course.enrollment.last_slide_index + 1 }} 页）
          </button>
        </div>

        <!-- 跨模块联动工具条 -->
        <div class="mt-4 flex flex-wrap gap-2 items-center">
          <span class="text-xs text-surface-500 font-medium">🔗 课程联动：</span>
          <button @click="askAboutCourse"
                  class="text-xs px-3 py-1.5 rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200">
            💬 就本课程提问 AI
          </button>
          <button v-if="coursewareDocs.length" @click="discussDocs"
                  class="text-xs px-3 py-1.5 rounded-md bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200"
                  title="把课件文本作为附件带去对话">
            📎 带 {{ coursewareDocs.length }} 份课件文本对话
          </button>
          <button @click="$router.push(`/knowledge?q=${encodeURIComponent(course.title)}`)"
                  class="text-xs px-3 py-1.5 rounded-md bg-surface-100 text-surface-600 hover:bg-surface-200 border border-surface-200">
            📚 搜索资料库
          </button>
          <button v-if="isTeacher" @click="$router.push(`/automation?prefillName=${encodeURIComponent(course.title + ' · 备课流水线')}&projectId=${course.project_id || ''}`)"
                  class="text-xs px-3 py-1.5 rounded-md bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200">
            ⚙️ 建备课流水线
          </button>
          <button v-if="course.project_id" @click="$router.push(`/project/${course.project_id}`)"
                  class="text-xs px-3 py-1.5 rounded-md bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200">
            📁 关联项目 #{{ course.project_id }}
          </button>
          <button v-if="isTeacher" @click="showEdit = true"
                  class="text-xs px-3 py-1.5 rounded-md bg-surface-100 text-surface-600 hover:bg-surface-200 border border-surface-200">
            ✏️ 编辑课程
          </button>
        </div>
      </div>

      <!-- ═══ 章节大纲 ═══ -->
      <div v-if="course.chapters?.length || course.syllabus" class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-semibold text-sm">🗂️ 教学大纲</h2>
          <button v-if="course.syllabus" @click="showSyllabus = !showSyllabus" class="text-xs text-primary-600 hover:underline">
            {{ showSyllabus ? '收起原文' : '查看大纲原文' }}
          </button>
        </div>
        <div v-if="course.chapters?.length" class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div v-for="(ch, i) in course.chapters" :key="i" class="p-3 rounded-lg bg-surface-50 border border-surface-100">
            <p class="text-sm font-medium">第 {{ i + 1 }} 章 · {{ ch.title }}</p>
            <div v-if="ch.points?.length" class="mt-1.5 flex flex-wrap gap-1">
              <span v-for="(p, j) in ch.points" :key="j" class="text-[11px] px-1.5 py-0.5 rounded bg-white border border-surface-200 text-surface-600">
                {{ p }}
              </span>
            </div>
          </div>
        </div>
        <pre v-if="showSyllabus" class="mt-3 text-xs text-surface-600 bg-surface-50 rounded-lg p-3 max-h-64 overflow-y-auto whitespace-pre-wrap font-mono">{{ course.syllabus }}</pre>

        <!-- 知识点图（可折叠） -->
        <div class="mt-4 pt-4 border-t border-surface-100">
          <button @click="graphOpen = !graphOpen" class="text-xs text-primary-600 hover:underline">
            {{ graphOpen ? '▲ 收起知识点图' : '▼ 展开知识点图' }}
          </button>
          <div v-if="graphOpen" class="mt-3" style="height: 400px">
            <GraphView scope="syllabus" :scope-id="course.id" :auto-load="false"
                       empty-tip="让 AI 从当前大纲抽取知识点关联图（需课程已录入大纲或章节）" />
          </div>
        </div>
      </div>

      <!-- ═══ 课件列表 ═══ -->
      <div class="card p-5">
        <div class="flex flex-wrap items-center justify-between gap-2 mb-4">
          <h2 class="font-semibold">📀 课件（{{ coursewares.length }}）</h2>
          <div v-if="isTeacher" class="flex flex-wrap gap-2">
            <label class="text-xs px-3 py-1.5 rounded-md bg-primary-600 text-white hover:bg-primary-700 cursor-pointer">
              ⬆️ 上传 PPT 电子化
              <input type="file" accept=".pptx,.ppt" class="hidden" @change="onPickFile" />
            </label>
            <button @click="showGenerate = true" class="text-xs px-3 py-1.5 rounded-md bg-purple-600 text-white hover:bg-purple-700">
              🤖 AI 生成课件
            </button>
            <button @click="showPipeline = true" class="text-xs px-3 py-1.5 rounded-md bg-accent-600 text-white hover:bg-accent-700">
              ⚙️ 从流水线转讲义
            </button>
          </div>
        </div>

        <div v-if="uploading" class="mb-3 p-3 rounded-lg bg-blue-50 border border-blue-100">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="text-blue-700">⏳ {{ uploadMsg }}</span>
            <span class="text-blue-600 font-medium">{{ uploadPct }}%</span>
          </div>
          <div class="h-1.5 rounded-full bg-blue-100 overflow-hidden">
            <div class="h-full bg-blue-500 transition-all" :style="{ width: uploadPct + '%' }"></div>
          </div>
        </div>

        <div v-if="!coursewares.length" class="py-10 text-center">
          <p class="text-3xl mb-2">📂</p>
          <p class="text-sm text-surface-500">
            {{ isTeacher ? '还没有课件 — 上传 PPT 会自动转成电子书；也可以让 AI 直接生成' : '老师还没有发布课件，稍后再来看看' }}
          </p>
        </div>

        <div v-else class="space-y-3">
          <div v-for="w in coursewares" :key="w.id"
               class="p-4 rounded-lg border border-surface-100 hover:border-primary-200 hover:shadow-sm transition-all">
            <div class="flex items-start gap-3">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
                   :class="w.source_type === 'ai_generated' ? 'bg-purple-100' : 'bg-blue-100'">
                {{ w.source_type === 'ai_generated' ? '🤖' : '📊' }}
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="text-sm font-medium">{{ w.title }}</span>
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-surface-100 text-surface-500 font-mono">v{{ w.version }}</span>
                  <span v-if="w.parent_id" class="text-[10px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-600">AI 更新自 #{{ w.parent_id }}</span>
                  <span v-if="w.status === 'converting'" class="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700">⏳ 电子化中</span>
                  <span v-else-if="w.status === 'failed'" class="text-[10px] px-1.5 py-0.5 rounded bg-red-50 text-red-600">✕ 失败</span>
                  <span v-else class="text-[10px] px-1.5 py-0.5 rounded bg-green-50 text-green-700">可阅读</span>
                </div>
                <div class="mt-1.5 flex flex-wrap items-center gap-2 text-[11px] text-surface-500">
                  <span>📄 {{ w.slide_count }} 页</span>
                  <span v-if="w.file_size">原文件 {{ fmtKB(w.file_size) }}</span>
                  <span v-if="w.read_size_kb">电子书 {{ w.read_size_kb }} KB</span>
                  <span v-if="w.doc_id" class="text-indigo-600" title="课件文本已进资料库，可被检索/作为对话附件">🔍 已入资料库</span>
                  <span class="text-surface-400">{{ fmtDate(w.created_at) }}</span>
                </div>
                <p v-if="w.status === 'failed'" class="mt-1.5 text-[11px] text-red-500">{{ w.error_message }}</p>
                <div v-else-if="staleSummary(w)" class="mt-2 p-2 rounded-md bg-orange-50 border border-orange-100">
                  <p class="text-[11px] text-orange-800">
                    ⚠️ 陈旧度体检：{{ staleSummary(w) }}
                    <span v-if="w.staleness?.scanned_at" class="text-orange-500"> · {{ fmtDate(w.staleness.scanned_at) }}</span>
                  </p>
                </div>
              </div>
              <div class="flex flex-col gap-1.5 items-end flex-shrink-0">
                <button @click="openReader(w.id)" :disabled="w.status !== 'ready'"
                        class="text-xs px-3 py-1.5 rounded-md bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40">
                  📖 阅读
                </button>
                <div class="flex gap-1.5">
                  <button @click="openEbook(w.id)" :disabled="w.status !== 'ready'"
                          class="text-[11px] px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 disabled:opacity-40"
                          title="在线电子书：封面 + 目录 + 分章阅读，可调字号/夜间模式">📕 电子书</button>
                  <a :href="coursewareApi.ebookUrl(w.id, 'pdf')" target="_blank" rel="noopener"
                     class="text-[11px] px-2 py-1 rounded-md bg-surface-100 text-surface-500 hover:bg-surface-200 text-center"
                     title="电子书 PDF：带封面、目录与页码，可打印、手机可读">PDF</a>
                  <a :href="coursewareApi.ebookUrl(w.id, 'epub')" target="_blank" rel="noopener"
                     class="text-[11px] px-2 py-1 rounded-md bg-surface-100 text-surface-500 hover:bg-surface-200 text-center"
                     title="EPUB：可导入手机/阅读器，带可跳转目录">EPUB</a>
                </div>
                <div class="flex gap-1.5">
                  <a :href="coursewareApi.handoutUrl(w.id, 'student', 'docx')" target="_blank" rel="noopener"
                     class="text-[11px] px-2.5 py-1 rounded-md bg-surface-100 text-surface-600 hover:bg-surface-200 text-center"
                     title="学生讲义 Word：要点 + 笔记留白 + 课后思考题">📄 讲义</a>
                  <a :href="coursewareApi.handoutUrl(w.id, 'student', 'pdf')" target="_blank" rel="noopener"
                     class="text-[11px] px-2 py-1 rounded-md bg-surface-100 text-surface-500 hover:bg-surface-200 text-center"
                     title="学生讲义 PDF：直接打印发给学生">PDF</a>
                </div>
                <template v-if="isTeacher">
                  <div class="flex gap-1.5">
                    <a :href="coursewareApi.handoutUrl(w.id, 'teacher', 'docx')" target="_blank" rel="noopener"
                       class="text-[11px] px-2.5 py-1 rounded-md bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200 text-center"
                       title="教师讲义 Word：含讲透解释、讲师速记、每章时长建议与陈旧页警示">🗒 教师讲义</a>
                    <a :href="coursewareApi.handoutUrl(w.id, 'teacher', 'pdf')" target="_blank" rel="noopener"
                       class="text-[11px] px-2 py-1 rounded-md bg-amber-50 text-amber-600 hover:bg-amber-100 border border-amber-200 text-center"
                       title="教师讲义 PDF">PDF</a>
                  </div>
                  <button @click="scanStaleness(w)" :disabled="w.status !== 'ready' || scanning === w.id"
                          class="text-[11px] px-2.5 py-1 rounded-md bg-orange-50 text-orange-700 hover:bg-orange-100 border border-orange-200 disabled:opacity-40">
                    {{ scanning === w.id ? '体检中…' : '🩺 AI 体检' }}
                  </button>
                  <a :href="coursewareApi.exportUrl(w.id)" :download="`课件_${w.id}.pptx`"
                     class="text-[11px] px-2.5 py-1 rounded-md bg-surface-100 text-surface-600 hover:bg-surface-200 text-center">
                    ⬇️ 导出 PPTX
                  </a>
                  <button @click="removeCourseware(w)" class="text-[11px] px-2.5 py-1 rounded-md text-red-500 hover:bg-red-50">删除</button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ 名册（教师） ═══ -->
      <div v-if="isTeacher" class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-semibold text-sm">🎒 学生名册（{{ students.length }}）</h2>
          <button @click="loadStudents" class="text-xs text-primary-600 hover:underline">刷新</button>
        </div>
        <div v-if="!students.length" class="text-sm text-surface-400 py-4 text-center">
          还没有学生选修 · 发布课程后学生即可在「公开课程」中加入
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs text-surface-500 border-b border-surface-100">
                <th class="pb-2 pr-3">学生</th><th class="pb-2 pr-3">单位</th>
                <th class="pb-2 pr-3">进度</th><th class="pb-2 pr-3">最后页</th><th class="pb-2">选课时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in students" :key="s.student_id" class="border-b border-surface-50">
                <td class="py-2 pr-3">{{ s.name }}</td>
                <td class="py-2 pr-3 text-surface-500 text-xs">{{ s.institution || '—' }}</td>
                <td class="py-2 pr-3">
                  <div class="flex items-center gap-2">
                    <div class="w-24 h-1.5 rounded-full bg-surface-100 overflow-hidden">
                      <div class="h-full bg-green-500" :style="{ width: s.progress + '%' }"></div>
                    </div>
                    <span class="text-xs text-surface-500">{{ s.progress }}%</span>
                  </div>
                </td>
                <td class="py-2 pr-3 text-xs text-surface-500">第 {{ s.last_slide + 1 }} 页</td>
                <td class="py-2 text-xs text-surface-400">{{ fmtDate(s.enrolled_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ═══ AI 生成课件（需求 4） ═══ -->
      <Teleport to="body">
        <div v-if="showGenerate" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-start justify-center p-4 overflow-y-auto"
             @click.self="showGenerate = false">
          <div class="bg-white dark:bg-surface-900 rounded-xl shadow-2xl w-full max-w-2xl my-8">
            <div class="px-5 py-4 border-b border-surface-100 flex items-center justify-between">
              <h3 class="font-semibold">🤖 AI 快速生成课件</h3>
              <button @click="showGenerate = false" class="text-surface-400 hover:text-surface-600 text-xl leading-none">×</button>
            </div>
            <div class="p-5 space-y-4">
              <p class="text-xs text-surface-500 leading-relaxed">
                针对新课程，AI 会依据大纲 + 你勾选的系统素材直接产出可阅读的课件；
                生成后可继续电子书阅读、导出 .pptx 投影，或再跑一次体检刷新。
              </p>
              <div>
                <label class="block text-xs font-medium text-surface-600 mb-1">主题 / 章节标题 *</label>
                <input v-model.trim="gen.topic" class="input-field text-sm" :placeholder="course.title + ' · 例如：注意力机制与前向传播'" />
              </div>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div>
                  <label class="block text-[11px] font-medium text-surface-600 mb-1">章节数</label>
                  <input v-model.number="gen.chapter_count" type="number" min="1" max="20" class="input-field text-sm" />
                </div>
                <div>
                  <label class="block text-[11px] font-medium text-surface-600 mb-1">每章页数</label>
                  <input v-model.number="gen.slides_per_chapter" type="number" min="1" max="12" class="input-field text-sm" />
                </div>
                <div>
                  <label class="block text-[11px] font-medium text-surface-600 mb-1">受众</label>
                  <select v-model="gen.audience" class="input-field text-sm">
                    <option>本科生</option><option>研究生</option><option>工程人员</option><option>入门大众</option>
                  </select>
                </div>
                <div>
                  <label class="block text-[11px] font-medium text-surface-600 mb-1">风格</label>
                  <select v-model="gen.style" class="input-field text-sm">
                    <option>标准</option><option>深入推导</option><option>案例驱动</option><option>研究进展</option>
                  </select>
                </div>
              </div>
              <div>
                <label class="block text-[11px] font-medium text-surface-600 mb-1">🧠 生成模型（可选）</label>
                <div class="flex items-center gap-2">
                  <button type="button" @click="cycleModel(-1)" title="上一个模型" v-if="models.length"
                          class="px-1.5 py-1 text-xs rounded-md border border-surface-200 text-surface-500 hover:bg-surface-100">◀</button>
                  <select v-model="gen.model" class="input-field text-sm">
                    <option value="">🤖 默认模型（{{ defaultModel || '后端配置' }}）</option>
                    <optgroup v-for="g in modelGroups" :key="g.provider" :label="g.label">
                      <option v-for="m in g.items" :key="m.value" :value="m.value">{{ m.label }} — {{ m.desc }}</option>
                    </optgroup>
                  </select>
                  <button type="button" @click="cycleModel(1)" title="下一个模型" v-if="models.length"
                          class="px-1.5 py-1 text-xs rounded-md border border-surface-200 text-surface-500 hover:bg-surface-100">▶</button>
                </div>
              </div>
              <div>
                <label class="block text-xs font-medium text-surface-600 mb-1">补充要求（可选）</label>
                <textarea v-model="gen.syllabus" class="input-field text-sm h-20"
                          :placeholder="course.syllabus ? '留空则使用课程大纲：' + course.syllabus.slice(0, 60) + '…' : '例如：需要包含 2 个课堂练习与 1 个前沿论文案例'"></textarea>
              </div>

              <MaterialSourcePicker v-model="gen.sources" />

              <div class="text-[11px] text-surface-500 flex items-center gap-2">
                <span>预计产出 {{ gen.chapter_count * gen.slides_per_chapter }} 页</span>
                <span v-if="countSources(gen.sources)">·  引用 {{ countSources(gen.sources) }} 个素材源</span>
              </div>
            </div>
            <div v-if="genBusy && genJob" class="px-5 pb-3 space-y-2">
              <div class="flex items-center justify-between text-xs gap-2">
                <span class="text-purple-700 truncate">{{ genJob.message || '生成中…' }}</span>
                <span class="font-mono text-surface-500 shrink-0">{{ genJob.percent }}% · {{ genElapsed }}s{{ etaText }}</span>
              </div>
              <div class="h-2 rounded-full bg-surface-100 overflow-hidden">
                <div class="h-full rounded-full bg-gradient-to-r from-purple-500 to-primary-500 transition-all duration-700"
                     :style="{ width: `${genJob.percent}%` }"></div>
              </div>
              <p class="text-[10px] text-surface-500">
                章节 {{ genJob.chapters_done }}/{{ genJob.chapters_total }} · 已产出 {{ genJob.slides_done }} 页
              </p>
              <ul v-if="genLog.length" class="text-[10px] text-surface-400 space-y-0.5 max-h-20 overflow-y-auto">
                <li v-for="(l, i) in genLog" :key="i">{{ l }}</li>
              </ul>
            </div>
            <div class="px-5 py-4 border-t border-surface-100 flex items-center justify-between">
              <span v-if="genMsg" class="text-xs" :class="genCancelled ? 'text-amber-600' : genErr ? 'text-red-500' : 'text-green-600'">{{ genMsg }}</span>
              <div class="flex gap-2 ml-auto">
                <button @click="showGenerate = false" class="px-4 py-2 rounded-lg text-sm bg-surface-100 hover:bg-surface-200">关闭</button>
                <button v-if="genBusy" @click="stopGen" :disabled="!genJob?.job_id || genCancelling"
                        class="px-4 py-2 rounded-lg text-sm bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 disabled:opacity-50">
                  {{ genCancelling ? '⏹ 正在停止…' : '⏹ 停止生成' }}
                </button>
                <button v-else @click="runGenerate" :disabled="!gen.topic"
                        class="px-4 py-2 rounded-lg text-sm bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50">
                  ✨ 开始生成
                </button>
              </div>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- ═══ 从流水线转讲义 ═══ -->
      <Teleport to="body">
        <div v-if="showPipeline" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-start justify-center p-4 overflow-y-auto"
             @click.self="showPipeline = false">
          <div class="bg-white dark:bg-surface-900 rounded-xl shadow-2xl w-full max-w-xl my-8">
            <div class="px-5 py-4 border-b border-surface-100 flex items-center justify-between">
              <h3 class="font-semibold">⚙️ 走研究流水线产出讲义</h3>
              <button @click="showPipeline = false" class="text-surface-400 hover:text-surface-600 text-xl leading-none">×</button>
            </div>
            <div class="p-5 space-y-4">
              <p class="text-xs text-surface-500 leading-relaxed">
                选择一条已运行成功的流水线，把它各 Agent 的研究结论直接转成课件；
                还可以叠加技能（含自主 / git / webhook 外接技能）的运行结果。
              </p>
              <div>
                <label class="block text-xs font-medium text-surface-600 mb-1">流水线 *</label>
                <select v-model="sync.pipeline_id" class="input-field text-sm">
                  <option :value="''">请选择</option>
                  <option v-for="p in materials.pipelines" :key="p.id" :value="p.id">
                    {{ p.label }}（{{ p.steps }} 步）
                  </option>
                </select>
              </div>
              <div v-if="availableRuns.length">
                <label class="block text-xs font-medium text-surface-600 mb-1">运行记录（默认取最近一次成功）</label>
                <select v-model="sync.run_id" class="input-field text-sm">
                  <option :value="''">最近一次成功运行</option>
                  <option v-for="r in availableRuns" :key="r.id" :value="r.id">{{ r.label }} · {{ String(r.id).slice(0, 8) }}</option>
                </select>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-[11px] font-medium text-surface-600 mb-1">章节数</label>
                  <input v-model.number="sync.chapter_count" type="number" min="1" max="15" class="input-field text-sm" />
                </div>
                <div>
                  <label class="block text-[11px] font-medium text-surface-600 mb-1">每章页数</label>
                  <input v-model.number="sync.slides_per_chapter" type="number" min="1" max="10" class="input-field text-sm" />
                </div>
              </div>
              <div>
                <label class="block text-xs font-medium text-surface-600 mb-1">讲义主题（可选）</label>
                <input v-model.trim="sync.topic" class="input-field text-sm" :placeholder="course.title" />
              </div>
              <div>
                <label class="block text-xs font-medium text-surface-600 mb-1">叠加运行技能（可选）</label>
                <div class="max-h-32 overflow-y-auto border border-surface-200 rounded-lg p-2 space-y-1">
                  <label v-for="s in materials.skills.slice(0, 40)" :key="s.id"
                         class="flex items-center gap-2 text-xs cursor-pointer hover:bg-surface-50 rounded px-1 py-0.5">
                    <input type="checkbox" class="accent-primary-600" :checked="sync.skill_ids.includes(s.id)"
                           @change="toggleSkill(s.id)" />
                    <span class="truncate">{{ s.label }}</span>
                    <span class="ml-auto text-[10px] text-surface-400">{{ s.type }}</span>
                  </label>
                </div>
              </div>
            </div>
            <div class="px-5 py-4 border-t border-surface-100 flex items-center justify-between">
              <span v-if="syncMsg" class="text-xs" :class="syncErr ? 'text-red-500' : 'text-green-600'">{{ syncMsg }}</span>
              <div class="flex gap-2 ml-auto">
                <button @click="showPipeline = false" class="px-4 py-2 rounded-lg text-sm bg-surface-100 hover:bg-surface-200">关闭</button>
                <button @click="runSync" :disabled="syncBusy || !sync.pipeline_id"
                        class="px-4 py-2 rounded-lg text-sm bg-accent-600 text-white hover:bg-accent-700 disabled:opacity-50">
                  {{ syncBusy ? '⏳ 转换中…' : '🔄 生成讲义' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- ═══ 编辑课程 ═══ -->
      <Teleport to="body">
        <div v-if="showEdit" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-start justify-center p-4 overflow-y-auto"
             @click.self="showEdit = false">
          <div class="bg-white dark:bg-surface-900 rounded-xl shadow-2xl w-full max-w-xl my-8">
            <div class="px-5 py-4 border-b border-surface-100 flex items-center justify-between">
              <h3 class="font-semibold">✏️ 编辑课程</h3>
              <button @click="showEdit = false" class="text-surface-400 hover:text-surface-600 text-xl leading-none">×</button>
            </div>
            <div class="p-5 space-y-3">
              <div><label class="block text-xs font-medium text-surface-600 mb-1">课程名称</label>
                <input v-model.trim="edit.title" class="input-field text-sm" /></div>
              <div class="grid grid-cols-3 gap-3">
                <div><label class="block text-xs font-medium text-surface-600 mb-1">编号</label>
                  <input v-model.trim="edit.code" class="input-field text-sm" /></div>
                <div><label class="block text-xs font-medium text-surface-600 mb-1">领域</label>
                  <input v-model.trim="edit.domain" class="input-field text-sm" /></div>
                <div><label class="block text-xs font-medium text-surface-600 mb-1">Emoji</label>
                  <input v-model.trim="edit.cover_emoji" class="input-field text-sm" /></div>
              </div>
              <div><label class="block text-xs font-medium text-surface-600 mb-1">简介</label>
                <textarea v-model="edit.description" class="input-field text-sm h-20"></textarea></div>
              <div><label class="block text-xs font-medium text-surface-600 mb-1">教学大纲</label>
                <textarea v-model="edit.syllabus" class="input-field text-sm h-28 font-mono"></textarea></div>
              <div><label class="block text-xs font-medium text-surface-600 mb-1">可见性</label>
                <select v-model="edit.visibility" class="input-field text-sm">
                  <option value="public">公开</option><option value="private">仅自己</option>
                </select></div>
            </div>
            <div class="px-5 py-4 border-t border-surface-100 flex items-center justify-between">
              <button @click="removeCourse" class="text-xs text-red-500 hover:underline">删除此课程</button>
              <div class="flex gap-2">
                <button @click="showEdit = false" class="px-4 py-2 rounded-lg text-sm bg-surface-100 hover:bg-surface-200">取消</button>
                <button @click="saveEdit" :disabled="savingEdit"
                        class="px-4 py-2 rounded-lg text-sm bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50">
                  {{ savingEdit ? '保存中…' : '保存' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Teleport>
    </template>

    <div v-else class="card p-10 text-center">
      <p class="text-3xl mb-2">🔍</p>
      <p class="text-sm text-surface-500">{{ loadError || '课程不存在或无权访问' }}</p>
      <button @click="$router.push('/courses')" class="mt-3 text-sm text-primary-600 hover:underline">返回课程中心</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { courseApi, coursewareApi, uploadProgress, type Course, type CoursewareBrief, type MaterialSources, type MaterialSelection, type GenerateJobStatus, type GenerateModelItem, type GenerateModelGroup } from '@/api/modules/courses'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import MaterialSourcePicker from '@/components/course/MaterialSourcePicker.vue'
import GraphView from '@/components/common/GraphView.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const appStore = useAppStore()

const courseId = computed(() => Number(route.params.id || 0))
const loading = ref(true)
const loadError = ref('')
const course = ref<Course | null>(null)
const coursewares = ref<CoursewareBrief[]>([])
const students = ref<any[]>([])
const isTeacher = ref(false)
const showSyllabus = ref(false)
const graphOpen = ref(false)
const scanning = ref<number | null>(null)

const materials = reactive<MaterialSources>({
  documents: [], questions: [], tasks: [], projects: [], pipelines: [], pipeline_runs: [], skills: [],
})

const coursewareDocs = computed(() => coursewares.value.filter(w => w.doc_id))

function staleSummary(w: CoursewareBrief) {
  const s: any = w.staleness?.summary
  if (!s) return ''
  const stale = s.stale ?? s.needs_update ?? s.risky ?? s.high_risk ?? s.outdated ?? 0
  if (!stale) return s.ok ? '' : ''
  return `${stale} 页内容可能过时${s.total ? ` / 共 ${s.total} 页` : ''}${s.categories ? '（' + Object.entries(s.categories).slice(0, 3).map(([k, v]) => `${k}:${v}`).join('、') + '）' : ''}`
}

function fmtKB(b: number) {
  if (!b) return '0'
  return b > 1024 * 1024 ? (b / 1048576).toFixed(1) + ' MB' : Math.round(b / 1024) + ' KB'
}
function fmtDate(s: string) {
  if (!s) return ''
  const d = new Date(s)
  return isNaN(d.getTime()) ? s.slice(0, 10) : `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function loadCourse() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await courseApi.detail(courseId.value)
    course.value = res.data
    coursewares.value = res.data.coursewares || []
    isTeacher.value = !!res.data.is_teacher
    if (isTeacher.value) loadStudents()
    if (route.query.new === '1' && isTeacher.value) showGenerate.value = true
  } catch (e: any) {
    loadError.value = e?.response?.data?.detail || '加载失败'
  } finally { loading.value = false }
}

async function loadStudents() {
  try { students.value = (await courseApi.students(courseId.value)).data.items || [] } catch { /* ignore */ }
}

async function loadMaterials() {
  try { Object.assign(materials, (await courseApi.materials(40)).data) } catch { /* ignore */ }
}

function openReader(cwId: number) { router.push(`/course/${courseId.value}/read/${cwId}`) }
/** 在线电子书（独立阅读页，不是下载） */
function openEbook(cwId: number) {
  router.push({ name: 'CoursewareEbook', params: { courseId: courseId.value, cwId } })
}

// ═══ 选课 ═══
async function toggleEnroll() {
  try {
    if (course.value?.is_enrolled) { await courseApi.unenroll(courseId.value) }
    else { await courseApi.enroll(courseId.value) }
    await loadCourse()
  } catch (e: any) { alert(e?.response?.data?.detail || '操作失败') }
}

async function setStatus(status: string) {
  try { await courseApi.update(courseId.value, { status } as any); await loadCourse() }
  catch (e: any) { alert(e?.response?.data?.detail || '状态更新失败') }
}

// ═══ 上传 PPT（需求 2） ═══
const uploading = ref(false)
const uploadPct = ref(0)
const uploadMsg = ref('')
async function onPickFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  input.value = ''
  if (!/\.pptx$/i.test(file.name)) {
    alert('请上传 .pptx（.ppt 请先在 Office 中另存为 .pptx）')
    return
  }
  uploading.value = true
  uploadPct.value = 0
  uploadMsg.value = `正在上传 ${file.name}（${fmtKB(file.size)}），服务端即将逐页拆解为电子书…`
  uploadProgress.cb = (p) => { uploadPct.value = p }
  try {
    const res = await courseApi.uploadCourseware(courseId.value, file, file.name.replace(/\.pptx$/i, ''))
    const opt: any = (res.data as any).optimization || {}
    uploadPct.value = 100
    uploadMsg.value = `电子化完成 · ${res.data.slide_count} 页` +
      (opt.first_paint_kb ? ` · 首屏 ${opt.first_paint_kb}KB（↓${opt.saved_percent ?? 0}%）` : '')
    await loadCourse()
    setTimeout(() => openReader(res.data.id), 700)
  } catch (err: any) {
    uploadMsg.value = ''
    alert(err?.response?.data?.detail || '上传/电子化失败')
  } finally {
    uploadProgress.cb = null
    setTimeout(() => { uploading.value = false }, 2600)
  }
}

async function removeCourseware(w: CoursewareBrief) {
  if (!confirm(`确定删除课件「${w.title}」？`)) return
  try { await coursewareApi.remove(w.id); await loadCourse() } catch (e: any) { alert(e?.response?.data?.detail || '删除失败') }
}

// ═══ AI 体检（需求 3） ═══
async function scanStaleness(w: CoursewareBrief) {
  scanning.value = w.id
  try {
    const res = await coursewareApi.stalenessScan(w.id)
    const s: any = res.data.summary || {}
    const stale = s.stale ?? s.needs_update ?? s.risky ?? s.high_risk ?? 0
    alert(`体检完成：${stale} 页疑似过时（花费 ¥${(res.data.cost || 0).toFixed(4)}）\n点击课件「阅读」即可查看逐页标注，并在阅读器中一键 AI 更新。`)
    await loadCourse()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '体检失败')
  } finally { scanning.value = null }
}

// ═══ AI 生成课件（需求 4，走课件工坊同一套作业接口，因此也有真实进度） ═══
const showGenerate = ref(false)
const genBusy = ref(false)
const genMsg = ref('')
const genErr = ref(false)
const genJob = ref<GenerateJobStatus | null>(null)
const genLog = ref<string[]>([])
const genElapsed = ref(0)
const genCancelling = ref(false)
const genCancelled = ref(false)
const models = ref<GenerateModelItem[]>([])
const modelGroups = ref<GenerateModelGroup[]>([])
const defaultModel = ref('')

// 线性 ETA（后端按 percent + 已用时长估算）
const etaText = computed(() => {
  const s = genJob.value?.eta_seconds
  if (genJob.value?.status !== 'running' || s == null) return ''
  return s >= 90 ? ` · 预计还需 ${Math.max(1, Math.round(s / 60))} 分钟` : ` · 预计还需 ${Math.round(s)} 秒`
})
let genPoll: number | null = null
let genTick: number | null = null
const gen = reactive<{ topic: string; syllabus: string; chapter_count: number; slides_per_chapter: number; style: string; audience: string; sources: MaterialSelection; model: string }>({
  topic: '', syllabus: '', chapter_count: 6, slides_per_chapter: 4, style: '标准', audience: '本科生', sources: {}, model: '',
})
function countSources(s: MaterialSelection) {
  return (s.doc_ids?.length || 0) + (s.question_ids?.length || 0) + (s.task_ids?.length || 0) +
    (s.project_id ? 1 : 0) + (s.chat_project_id ? 1 : 0) + (s.pipeline_run_id ? 1 : 0) + (s.skill_runs?.length || 0)
}

watch(showGenerate, (v) => {
  if (v) {
    gen.topic = gen.topic || (course.value?.title ? `${course.value.title} · 新章节` : '')
    loadMaterials()
    loadModels()
  }
})

function stopGenTimers() {
  if (genPoll) { window.clearInterval(genPoll); genPoll = null }
  if (genTick) { window.clearInterval(genTick); genTick = null }
}
onUnmounted(stopGenTimers)

/** 轮询生成作业：同一个 job 接口，阶段/章节/页数进度与课件工坊一致 */
async function pollGenerate(jobId: string) {
  try {
    const r = await coursewareApi.generateStatus(jobId)
    const s = r.data
    genJob.value = { ...s, percent: Math.max(s.percent || 0, genJob.value?.percent || 0) }
    if (s.message && !genLog.value.some(l => l.endsWith(s.message))) {
      genLog.value.push(`+${genElapsed.value}s ${s.message}`)
      if (genLog.value.length > 24) genLog.value.shift()
    }
    if (s.status === 'done' && s.result) {
      stopGenTimers()
      genBusy.value = false
      genCancelling.value = false
      genCancelled.value = false
      const d: any = s.result
      genMsg.value = `✅ 已生成 ${d.slide_count} 页 · 花费 ¥${(d.cost || 0).toFixed(4)}` +
        (d.sources_used?.length ? ` · 引用 ${d.sources_used.length} 个素材源` : '')
      await loadCourse()
      setTimeout(() => { showGenerate.value = false; if (d.courseware_id) openReader(d.courseware_id) }, 1200)
    } else if (s.status === 'failed') {
      stopGenTimers()
      genBusy.value = false
      genCancelling.value = false
      genErr.value = true
      genMsg.value = s.error ? `生成失败：${s.error}` : '生成失败，请稍后重试'
    } else if (s.status === 'cancelled') {
      stopGenTimers()
      genBusy.value = false
      genCancelling.value = false
      genCancelled.value = true
      genMsg.value = '已停止生成。调好参数后可直接重新开始。'
    }
  } catch (e: any) {
    if (e?.response?.status === 404) {
      stopGenTimers()
      genBusy.value = false
      genErr.value = true
      genMsg.value = '作业记录已过期，请在下方课件列表查看是否已生成'
    }
  }
}

async function runGenerate() {
  genBusy.value = true
  genMsg.value = ''
  genErr.value = false
  genCancelled.value = false
  genCancelling.value = false
  genLog.value = []
  genElapsed.value = 0
  genJob.value = {
    ok: true, job_id: '', status: 'running', stage: 'queued', percent: 1,
    message: '正在提交生成作业…', chapters_done: 0, chapters_total: gen.chapter_count,
    slides_done: 0, slides_total: 1 + gen.chapter_count * gen.slides_per_chapter,
  }
  genTick = window.setInterval(() => { genElapsed.value += 1 }, 1000)
  try {
    const res = await coursewareApi.startGenerate({
      topic: gen.topic, syllabus: gen.syllabus, chapter_count: gen.chapter_count,
      slides_per_chapter: gen.slides_per_chapter, style: gen.style, audience: gen.audience,
      domain: course.value?.domain, sources: gen.sources, course_id: courseId.value, auto_save: true,
      // 面板显式选择 > 顶栏全局首选 > 不传（后端按模式定档）
      model: gen.model || appStore.preferredModel || undefined,
    })
    const jobId = res.data.job_id
    if (!jobId) throw new Error('服务端未返回 job_id')
    genJob.value = { ...genJob.value, job_id: jobId }
    void pollGenerate(jobId)
    genPoll = window.setInterval(() => void pollGenerate(jobId), 1200)
  } catch (e: any) {
    stopGenTimers()
    genBusy.value = false
    genJob.value = null
    genErr.value = true
    genMsg.value = e?.response?.data?.detail || '生成失败，请稍后重试'
  }
}

/** 停止当前生成作业（服务端等当前步骤结束后停下）*/
async function stopGen() {
  const jobId = genJob.value?.job_id
  if (!jobId || genCancelling.value) return
  genCancelling.value = true
  try {
    await coursewareApi.cancelGenerate(jobId)
  } catch (e: any) {
    genCancelling.value = false
    if (e?.response?.status !== 409) genMsg.value = e?.response?.data?.detail || '停止失败，请重试'
  }
}

// 下拉两侧 ◀▶：在「默认 → 各模型」间循环切换
function cycleModel(dir: number) {
  const names = models.value.map(m => m.value)
  if (!names.length) return
  const ring = ['', ...names]
  const idx = ring.indexOf(gen.model)
  const next = (idx + dir + ring.length) % ring.length
  gen.model = ring[next]
}

async function loadModels() {
  if (models.value.length) return
  try {
    const r = await coursewareApi.generateModels()
    models.value = r.data?.items || []
    modelGroups.value = r.data?.groups?.length
      ? r.data.groups
      : (models.value.length ? [{ provider: 'default', label: '模型', items: models.value }] : [])
    defaultModel.value = r.data?.default || ''
  } catch { /* ignore */ }
}

// ═══ 流水线转讲义 ═══
const showPipeline = ref(false)
const syncBusy = ref(false)
const syncMsg = ref('')
const syncErr = ref(false)
const sync = reactive<{ pipeline_id: string; run_id: string; topic: string; chapter_count: number; slides_per_chapter: number; skill_ids: string[] }>({
  pipeline_id: '', run_id: '', topic: '', chapter_count: 5, slides_per_chapter: 4, skill_ids: [],
})
const availableRuns = computed(() => materials.pipeline_runs.filter(r => !sync.pipeline_id || r.pipeline_id === sync.pipeline_id))
function toggleSkill(id: string) {
  sync.skill_ids = sync.skill_ids.includes(id) ? sync.skill_ids.filter(x => x !== id) : [...sync.skill_ids, id]
}
watch(showPipeline, (v) => { if (v) loadMaterials() })
watch(() => sync.pipeline_id, () => { sync.run_id = '' })

async function runSync() {
  syncBusy.value = true
  syncMsg.value = ''
  syncErr.value = false
  try {
    const res = await courseApi.syncFromPipeline(courseId.value, {
      pipeline_id: sync.pipeline_id, run_id: sync.run_id || null, topic: sync.topic || undefined,
      chapter_count: sync.chapter_count, slides_per_chapter: sync.slides_per_chapter,
      skill_runs: sync.skill_ids.map(id => ({ skill_id: id })),
    })
    const d: any = res.data
    syncMsg.value = `✅ 已生成 ${d.slide_count} 页讲义（源流水线 ${d.pipeline?.name || ''}）`
    await loadCourse()
    setTimeout(() => { showPipeline.value = false; if (d.courseware_id) openReader(d.courseware_id) }, 1200)
  } catch (e: any) {
    syncErr.value = true
    syncMsg.value = e?.response?.data?.detail || '生成失败'
  } finally { syncBusy.value = false }
}

// ═══ 编辑课程 ═══
const showEdit = ref(false)
const savingEdit = ref(false)
const edit = reactive({ title: '', code: '', description: '', syllabus: '', domain: '', cover_emoji: '📖', visibility: 'public' })
watch(showEdit, (v) => {
  if (v && course.value) {
    const c = course.value
    Object.assign(edit, {
      title: c.title, code: c.code, description: c.description, syllabus: c.syllabus,
      domain: c.domain, cover_emoji: c.cover_emoji, visibility: c.visibility,
    })
  }
})
async function saveEdit() {
  savingEdit.value = true
  try { await courseApi.update(courseId.value, edit as any); showEdit.value = false; await loadCourse() }
  catch (e: any) { alert(e?.response?.data?.detail || '保存失败') }
  finally { savingEdit.value = false }
}
async function removeCourse() {
  if (!confirm('删除课程会同时移除其全部课件，确定？')) return
  try { await courseApi.remove(courseId.value); router.push('/courses') } catch (e: any) { alert(e?.response?.data?.detail || '删除失败') }
}

// ═══ 联动：把课程上下文带去对话 ═══
function askAboutCourse() {
  const ch = course.value?.chapters?.map((x, i) => `第${i + 1}章 ${x.title}`).join('、') || ''
  const prefill = `我正在学习课程《${course.value?.title}》（领域：${course.value?.domain || '未分类'}）。` +
    (ch ? `章节：${ch}。` : '') + ' 请先给我一份学习路线建议，并指出重点与难点。'
  const pid = course.value?.project_id || ''
  router.push(`/chat?projectId=${pid}&prefill=${encodeURIComponent(prefill)}&courseId=${courseId.value}`)
}
function discussDocs() {
  const ids = coursewareDocs.value.map(w => w.doc_id).filter(Boolean).join(',')
  const prefill = `基于这些课件文本，帮我出一份复习提纲与自测题：`
  router.push(`/chat?attachments=${encodeURIComponent(ids)}&prefill=${encodeURIComponent(prefill)}&courseId=${courseId.value}`)
}

onMounted(loadCourse)
watch(courseId, () => { if (courseId.value) loadCourse() })
</script>
