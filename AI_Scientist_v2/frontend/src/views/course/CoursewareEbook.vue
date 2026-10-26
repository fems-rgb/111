<template>
  <div class="ebook" :class="[`theme-${theme}`, { wide }]" :style="{ '--fs': `${fontSize}px` }">
    <!-- ═══ 顶栏：进度 / 字号 / 主题 / 目录 / 下载 ═══ -->
    <header class="bar">
      <div class="bar-left">
        <button class="btn ghost" @click="goBack" title="回到课程">← 返回</button>
        <div class="bar-title">
          <p class="bar-course">{{ meta?.course_title || '课程电子书' }}</p>
          <h1 class="truncate">{{ meta?.title || '加载中…' }}</h1>
        </div>
      </div>

      <div class="bar-right">
        <div class="bar-progress" :title="`已读 ${pct}%`">
          <span :style="{ width: `${pct}%` }"></span>
        </div>
        <span class="bar-pct">{{ pct }}%</span>
        <button class="btn" @click="tocOpen = !tocOpen" :class="{ on: tocOpen }">☰ 目录</button>
        <div class="stepper">
          <button class="btn sq" @click="bumpFont(-1)" :disabled="fontSize <= 15" title="缩小字号">A－</button>
          <button class="btn sq" @click="bumpFont(1)" :disabled="fontSize >= 24" title="放大字号">A＋</button>
        </div>
        <button class="btn" @click="cycleTheme" :title="`主题：${themeLabel}`">{{ themeIcon }}</button>
        <button class="btn" :class="{ on: showPlates }" @click="togglePlates" title="显示每页原版式插图">🖼 插图</button>
        <button v-if="meta?.is_teacher" class="btn" :class="{ on: showNotes }" @click="toggleNotes" title="显示讲师备注">🗒 备注</button>
        <a class="btn" :href="coursewareApi.ebookUrl(cwId, 'pdf')" target="_blank" rel="noopener" title="下载 PDF">PDF</a>
        <a class="btn" :href="coursewareApi.ebookUrl(cwId, 'epub')" target="_blank" rel="noopener" title="下载 EPUB">EPUB</a>
        <button class="btn ghost" @click="toSlides" title="切到幻灯片模式">🖥 幻灯片</button>
      </div>
    </header>

    <div class="body">
      <!-- ═══ 目录 ═══ -->
      <aside v-if="tocOpen || wide" class="toc" :class="{ drawer: !wide }">
        <div class="toc-head">
          <p>目录</p>
          <button v-if="!wide" class="btn ghost sq" @click="tocOpen = false">×</button>
        </div>
        <div class="toc-scroll">
          <template v-for="ch in chapters" :key="ch.uid">
            <button class="toc-ch" :class="{ active: activeChapter === ch.uid }" @click="goToChapter(ch)">
              <span class="toc-no">{{ ch.closing ? '结' : pad(ch.no) }}</span>
              <span class="toc-name">{{ ch.title }}</span>
              <span class="toc-count">{{ ch.pages.length }}</span>
            </button>
            <div class="toc-pages">
              <button v-for="p in ch.pages" :key="p.slide_index" class="toc-page"
                      :class="{ active: activePage === p.slide_index }"
                      @click="goToPage(p)">
                <span class="dot"></span>{{ p.title }}
              </button>
            </div>
          </template>
          <div v-if="closingItems.length" class="toc-pages">
            <button class="toc-page" @click="scrollTo('book-end')">
              <span class="dot"></span>课后 · 思考与延伸
            </button>
          </div>
        </div>
      </aside>
      <div v-if="tocOpen && !wide" class="toc-mask" @click="tocOpen = false"></div>

      <!-- ═══ 正文 ═══ -->
      <main class="main">
        <div v-if="loading" class="state">⏳ 正在排版电子书…</div>
        <div v-else-if="!meta" class="state">📕 没有找到这份课件</div>

        <template v-else>
          <!-- 封面 -->
          <section class="cover">
            <p class="cover-kicker">{{ meta.domain || meta.course_title || '课程电子书' }}</p>
            <h1 class="cover-title">{{ meta.title }}</h1>
            <div class="cover-rule"></div>
            <p class="cover-lead">{{ coverLead }}</p>
            <p class="cover-meta">
              {{ meta.course_title }} · 共 {{ contentChapters }} 章 {{ totalPages }} 节 · 约 {{ readingMinutes }} 分钟
              <span v-if="meta.version > 1"> · v{{ meta.version }}</span>
            </p>
            <button class="cover-start" @click="startReading">开始阅读 →</button>
            <p v-if="meta.is_teacher" class="cover-tip">教师视图：可打开「备注」查看每页讲师速记</p>
          </section>

          <!-- 章节 -->
          <article v-for="ch in chapters" :key="ch.uid" :id="`ch-${ch.uid}`" class="chapter">
            <header class="ch-head">
              <p class="ch-kicker">{{ ch.closing ? '结课' : `第 ${ch.no} 章` }}</p>
              <h2>{{ ch.title }}</h2>
              <p v-if="ch.question" class="ch-question">本章要解决：{{ ch.question }}</p>
            </header>

            <section v-for="p in ch.pages" :key="p.slide_index" :id="`pg-${p.slide_index}`"
                     :data-page="p.slide_index" class="page">
              <p v-if="p.kicker" class="eyebrow">{{ p.kicker }}</p>
              <h3 class="page-title"><span class="seq">{{ pad(p.seq) }}</span>{{ p.title }}</h3>
              <p v-if="p.lead" class="dek">{{ p.lead }}</p>

              <p v-for="(para, i) in splitParagraphs(p.detail)" :key="`d${i}`" class="para">{{ para }}</p>

              <!-- 要点 -->
              <ul v-if="p.bullets?.length" class="points">
                <li v-for="(b, i) in p.bullets" :key="i" :class="{ sub: b.level >= 1 }">
                  <span class="pt-dot"></span><span>{{ b.text }}</span>
                </li>
              </ul>

              <!-- 卡片 -->
              <div v-if="p.cards?.length" class="cards" :style="{ gridTemplateColumns: `repeat(${Math.min(p.cards?.length || 1, 2)}, minmax(0,1fr))` }">
                <div v-for="(c, i) in p.cards" :key="i" class="mini-card">
                  <p class="mini-title">{{ c.title }}</p>
                  <p class="mini-desc">{{ c.desc }}</p>
                </div>
              </div>

              <!-- 对比 -->
              <div v-if="p.compare" class="compare">
                <div class="cmp-col">
                  <p class="cmp-title">{{ p.compare.left?.title }}</p>
                  <ul><li v-for="(t, i) in (p.compare.left?.items || [])" :key="i">{{ t }}</li></ul>
                </div>
                <div class="cmp-col right">
                  <p class="cmp-title">{{ p.compare.right?.title }}</p>
                  <ul><li v-for="(t, i) in (p.compare.right?.items || [])" :key="i">{{ t }}</li></ul>
                </div>
              </div>

              <!-- 关键数字 -->
              <div v-if="p.metrics?.length" class="metrics">
                <div v-for="(m, i) in p.metrics" :key="i" class="metric">
                  <p class="metric-val">{{ m.value }}<span class="metric-unit">{{ m.unit }}</span></p>
                  <p class="metric-label">{{ m.label }}</p>
                </div>
              </div>

              <!-- 数据图（用文字条呈现，阅读器里不抢版面） -->
              <figure v-if="p.chart?.labels?.length" class="chart">
                <figcaption class="chart-cap">
                  {{ p.chart?.series_name || '数据' }}<span v-if="p.chart?.unit">（{{ p.chart?.unit }}）</span>
                </figcaption>
                <div v-for="(label, i) in (p.chart?.labels || [])" :key="i" class="chart-row">
                  <span class="chart-label">{{ label }}</span>
                  <span class="chart-track"><span class="chart-fill" :style="{ width: `${barPct(p.chart?.values?.[i] || 0, p.chart?.values || [])}%` }"></span></span>
                  <span class="chart-val">{{ p.chart?.values?.[i] }}</span>
                </div>
                <p v-if="p.chart?.caption" class="chart-note">数据来源：{{ p.chart?.caption }}</p>
              </figure>

              <!-- 流程 -->
              <ol v-if="p.steps?.length" class="flow">
                <li v-for="(s, i) in p.steps" :key="i" class="flow-step">
                  <span class="flow-no">{{ i + 1 }}</span>
                  <div>
                    <p class="flow-title">{{ s.title }}</p>
                    <p v-if="s.desc" class="flow-desc">{{ s.desc }}</p>
                  </div>
                </li>
              </ol>

              <!-- 表格 -->
              <div v-if="p.tables?.length" class="table-wrap">
                <table>
                  <tbody>
                    <tr v-for="(row, ri) in p.tables[0]" :key="ri">
                      <td v-for="(cell, ci) in row" :key="ci" :class="{ th: ri === 0 }">{{ cell }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 金句 -->
              <blockquote v-if="p.quote" class="quote">
                {{ p.quote }}<cite v-if="p.quote_by">—— {{ p.quote_by }}</cite>
              </blockquote>

              <!-- 案例 -->
              <aside v-if="p.example" class="callout example">
                <p class="callout-label">案例 / 例题</p>
                <p>{{ p.example }}</p>
              </aside>

              <!-- 带走三句话 -->
              <aside v-if="p.takeaway?.length" class="callout takeaway">
                <p class="callout-label">本节带走三句话</p>
                <ul><li v-for="(t, i) in p.takeaway" :key="i">{{ t }}</li></ul>
              </aside>

              <!-- 原版式插图 -->
              <figure v-if="showPlates && p.has_image" class="plate">
                <img :src="coursewareApi.imageUrl(cwId, p.slide_index)" loading="lazy" alt="" @error="hideImg" />
                <figcaption>原版式 · 第 {{ p.slide_index + 1 }} 页</figcaption>
              </figure>

              <!-- 讲师备注 -->
              <aside v-if="showNotes && p.notes" class="callout notes">
                <p class="callout-label">讲师备注</p>
                <p>{{ p.notes }}</p>
              </aside>

              <p v-if="p.risk_score >= 0.4" class="risk">⚠ 本页内容可能陈旧：{{ p.ai_suggestion || p.ai_reason }}</p>
            </section>
          </article>

          <!-- 结课：思考题 + 延伸阅读 -->
          <section v-if="closingItems.length" id="book-end" class="closing">
            <h2>课后 · 思考与延伸</h2>
            <div v-for="(blk, i) in closingItems" :key="i" class="closing-block">
              <p class="closing-title">{{ blk.title }}</p>
              <ul>
                <li v-for="(t, j) in blk.items" :key="j">{{ t }}</li>
              </ul>
            </div>
          </section>

          <!-- 翻页 -->
          <nav class="pager">
            <button class="pager-btn" :disabled="activeIdx <= 0" @click="stepPage(-1)">← 上一节</button>
            <span class="pager-mid">{{ activeIdx + 1 }} / {{ flatPages.length }}</span>
            <button class="pager-btn" :disabled="activeIdx >= flatPages.length - 1" @click="stepPage(1)">下一节 →</button>
          </nav>

          <footer class="foot">
            《{{ meta.title }}》 · {{ meta.course_title }} · 共 {{ totalPages }} 节
            <span class="foot-tip">快捷键 ← → 翻节 · 点击右上「PDF / EPUB」可下载到本地</span>
          </footer>
        </template>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { coursewareApi, type CoursewareDetail, type SlideMeta } from '@/api/modules/courses'

const route = useRoute()
const router = useRouter()

const cwId = computed(() => Number(route.params.cwId || 0))
const courseId = computed(() => Number(route.params.courseId || 0))

const meta = ref<CoursewareDetail | null>(null)
const loading = ref(true)
const tocOpen = ref(false)
const wide = ref(window.innerWidth >= 1180)

// 阅读偏好（字号/主题/插图/备注）按浏览器本地记住
const fontSize = ref(Number(localStorage.getItem('ebook_fs') || 18))
const theme = ref<'paper' | 'sepia' | 'night'>((localStorage.getItem('ebook_theme') as any) || 'paper')
const showPlates = ref(localStorage.getItem('ebook_plates') === '1')
const showNotes = ref(false)
const themeLabel = computed(() => ({ paper: '纸白', sepia: '护眼', night: '夜间' } as const)[theme.value])
const themeIcon = computed(() => ({ paper: '☀️', sepia: '🌿', night: '🌙' } as const)[theme.value])

const activePage = ref(0)
const activeChapter = ref(1)
let observer: IntersectionObserver | null = null

const coverSlide = computed(() => meta.value?.slides.find((s) => s.layout === 'cover'))
const coverLead = computed(() => {
  const raw = (coverSlide.value?.lead || '').trim()
  // 封面页的导语是生成时写的，常带着「共 6 章 · 约 24 页」这类当时参数，
  // 与下文实际章/节数对不上，宁可不显示也不用两套数字
  if (raw && !/共\s*\d+\s*章|约\s*\d+\s*页|\d+\s*页/.test(raw)) return raw
  return meta.value
    ? `把 ${meta.value.slide_count} 页课件重新编排成书，按章连续阅读；可调字号、开插图、切夜间模式。`
    : ''
})

/** 跳开封面/结课页，按 chapter 连续分组（上传课件没有章名时归入「正文」） */
const chapters = computed(() => {
  const slides = meta.value?.slides || []
  // key 只用于分组，title 可能被章节过渡页改写，两者必须分开
  const groups: { key: string; title: string; question?: string; pages: SlideMeta[] }[] = []
  let seq = 0
  for (const s of slides) {
    if (s.layout === 'cover' || s.layout === 'end') continue
    const name = (s.chapter || '').trim() || '正文'
    if (['封面', '封面页', '结课', '结束', '谢谢'].includes(name)) continue
    const last = groups[groups.length - 1]
    if (!last || last.key !== name) groups.push({ key: name, title: name, question: s.key_question, pages: [] })
    const g = groups[groups.length - 1]
    // 章节过渡页只用来做章标题，不单独占一节
    if (s.layout === 'section') {
      g.question = g.question || s.key_question
      if (!g.pages.length && s.title) g.title = s.title
      continue
    }
    g.pages.push({ ...s, seq: ++seq } as SlideMeta & { seq: number })
  }
  // 「小结/全课回顾」这类不算正文章，单独标成结课节（不占用第 N 章号）
  const CLOSING = ['小结', '总结', '结课', '全课回顾', '课程回顾']
  let chapterNo = 0
  return groups
    .filter((g) => g.pages.length)
    .map((g, i) => {
      const closing = CLOSING.some((k) => g.title.includes(k))
      if (!closing) chapterNo += 1
      return {
        uid: i + 1,
        no: closing ? chapterNo + 1 : chapterNo,
        closing, title: g.title, question: g.question,
        pages: g.pages as (SlideMeta & { seq: number })[],
      }
    })
})

const flatPages = computed(() => chapters.value.flatMap((c) => c.pages))
const totalPages = computed(() => flatPages.value.length)
const contentChapters = computed(() => chapters.value.filter((c) => !c.closing).length)

const totalChars = computed(() =>
  flatPages.value.reduce((n, p) => n + (p.detail?.length || 0) + (p.lead?.length || 0)
    + (p.bullets || []).reduce((m, b) => m + (b.text?.length || 0), 0), 0))
const readingMinutes = computed(() => Math.max(1, Math.round(totalChars.value / 420)))

const activeIdx = computed(() => {
  const i = flatPages.value.findIndex((p) => p.slide_index === activePage.value)
  return i < 0 ? 0 : i
})
const pct = computed(() =>
  totalPages.value ? Math.min(100, Math.round((activeIdx.value / Math.max(1, totalPages.value - 1)) * 100)) : 0)

const closingItems = computed(() => {
  const rep: Record<string, any> = meta.value?.staleness || {}
  const out: { title: string; items: string[] }[] = []
  if (rep.exercises?.length) out.push({ title: '课后思考', items: rep.exercises })
  if (rep.reading?.length) out.push({ title: '延伸阅读', items: rep.reading })
  return out
})

function pad(n: number) { return String(n).padStart(2, '0') }

/** 把「讲透」切成 1-3 段，避免整页一大坨字 */
function splitParagraphs(text?: string): string[] {
  const t = (text || '').trim()
  if (!t) return []
  const sents = t.split(/(?<=[。！？；])/).filter((x) => x.trim())
  const out: string[] = []
  let buf = ''
  for (const s of sents) {
    if (buf && buf.length + s.length > 70) { out.push(buf); buf = '' }
    buf += s
  }
  if (buf) out.push(buf)
  return out.slice(0, 3)
}

function barPct(v: number, arr: number[]) {
  const max = Math.max(...arr, 0.0001)
  return Math.max(2, Math.round((v / max) * 100))
}

function hideImg(e: Event) {
  const el = e.target as HTMLImageElement
  if (el) el.style.display = 'none'
}

// ── 滚动定位 ────────────────────────────────────────────────
function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ block: 'start', behavior: 'smooth' })
}
function goToChapter(ch: { uid: number }) {
  scrollTo(`ch-${ch.uid}`)
  if (!wide.value) tocOpen.value = false
}
function goToPage(p: SlideMeta & { seq: number }) {
  scrollTo(`pg-${p.slide_index}`)
  if (!wide.value) tocOpen.value = false
  window.localStorage.setItem(`ebook_at_${cwId.value}`, String(p.slide_index))
}
function startReading() {
  const first = flatPages.value[0]
  if (first) scrollTo(`pg-${first.slide_index}`)
}
function stepPage(dir: number) {
  const next = flatPages.value[activeIdx.value + dir]
  if (next) goToPage(next)
}

function observePages() {
  observer?.disconnect()
  observer = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (!e.isIntersecting) continue
      const idx = Number((e.target as HTMLElement).dataset.page || 0)
      activePage.value = idx
      const ch = chapters.value.find((c) => c.pages.some((p) => p.slide_index === idx))
      if (ch) activeChapter.value = ch.uid
      window.localStorage.setItem(`ebook_at_${cwId.value}`, String(idx))
      break
    }
  }, { rootMargin: '-25% 0px -60% 0px', threshold: 0 })
  document.querySelectorAll('[data-page]').forEach((el) => observer!.observe(el))
}

function onKey(e: KeyboardEvent) {
  const t = e.target as HTMLElement
  if (t && ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName)) return
  if (e.key === 'ArrowRight') { e.preventDefault(); stepPage(1) }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); stepPage(-1) }
  else if (e.key === 'Escape' && !wide.value) tocOpen.value = false
}
function onResize() { wide.value = window.innerWidth >= 1180 }

// ── 操作 ────────────────────────────────────────────────────
function bumpFont(d: number) {
  fontSize.value = Math.min(24, Math.max(15, fontSize.value + d))
  localStorage.setItem('ebook_fs', String(fontSize.value))
}
function cycleTheme() {
  theme.value = theme.value === 'paper' ? 'sepia' : theme.value === 'sepia' ? 'night' : 'paper'
  localStorage.setItem('ebook_theme', theme.value)
}
function togglePlates() {
  showPlates.value = !showPlates.value
  localStorage.setItem('ebook_plates', showPlates.value ? '1' : '0')
}
function toggleNotes() { showNotes.value = !showNotes.value }
function goBack() { router.push(courseId.value ? `/course/${courseId.value}` : '/courses') }
function toSlides() {
  router.push({ name: 'CoursewareReader', params: { courseId: courseId.value, cwId: cwId.value } })
}

watch(activePage, () => {
  // 章节高亮随滚动更新（放在这里避免 IntersectionObserver 里再算一遍）
  const ch = chapters.value.find((c) => c.pages.some((p) => p.slide_index === activePage.value))
  if (ch) activeChapter.value = ch.uid
})

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  window.addEventListener('resize', onResize)
  try {
    meta.value = await coursewareApi.detail(cwId.value).then((r) => r.data)
    if (meta.value?.is_teacher) showNotes.value = localStorage.getItem('ebook_notes') === '1'
  } catch {
    meta.value = null
  } finally {
    loading.value = false
  }
  await nextTick()
  observePages()
  // 恢复上次阅读位置
  const at = Number(localStorage.getItem(`ebook_at_${cwId.value}`) || 0)
  if (at > 0) setTimeout(() => scrollTo(`pg-${at}`), 120)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  window.removeEventListener('resize', onResize)
  observer?.disconnect()
  localStorage.setItem('ebook_notes', showNotes.value ? '1' : '0')
})
</script>

<style scoped>
.ebook {
  --bg: #fbfbf8;
  --panel: #ffffff;
  --ink: #1f2937;
  --ink-soft: #374151;
  --muted: #6b7280;
  --line: #e5e7eb;
  --accent: #4338ca;
  --accent-soft: #eef2ff;
  --warm: #b45309;
  --warm-soft: #fffbeb;
  --fs: 18px;
  min-height: 100vh;
  background: var(--bg);
  color: var(--ink);
  font-family: Georgia, "Songti SC", "SimSun", "Noto Serif SC", serif;
}
.ebook.theme-sepia { --bg: #f6efe1; --panel: #fbf5e9; --ink: #3b3226; --ink-soft: #4b4133; --muted: #7c6f5c; --line: #e2d6c0; --accent: #8a5a1f; --accent-soft: #f3e7cf; --warm-soft: #f7ecd8; }
.ebook.theme-night { --bg: #101319; --panel: #171b23; --ink: #e5e7eb; --ink-soft: #cbd5e1; --muted: #94a3b8; --line: #262c38; --accent: #a5b4fc; --accent-soft: #1e2433; --warm: #fbbf24; --warm-soft: #221f14; }

/* 顶栏 */
.bar { position: sticky; top: 0; z-index: 30; display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 18px; background: color-mix(in srgb, var(--bg) 88%, transparent); backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); font-family: system-ui, "Microsoft YaHei", sans-serif; }
.bar-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.bar-course { font-size: 11px; color: var(--muted); }
.bar-title h1 { font-size: 14px; font-weight: 600; margin-top: 1px; max-width: 42vw; }
.bar-right { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.bar-progress { width: 84px; height: 4px; border-radius: 999px; background: var(--line); overflow: hidden; }
.bar-progress span { display: block; height: 100%; background: var(--accent); transition: width .3s; }
.bar-pct { font-size: 11px; color: var(--muted); font-variant-numeric: tabular-nums; width: 30px; }
.stepper { display: flex; }
.btn { font-size: 12px; padding: 5px 9px; border-radius: 7px; border: 1px solid var(--line); background: var(--panel); color: var(--ink-soft); cursor: pointer; }
.btn:hover { border-color: var(--accent); color: var(--accent); }
.btn.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }
.btn.ghost { background: transparent; }
.btn.sq { padding: 5px 8px; }
.btn:disabled { opacity: .4; cursor: not-allowed; }
a.btn { text-decoration: none; }

/* 布局 */
.body { display: flex; max-width: 1240px; margin: 0 auto; }
.toc { width: 258px; flex-shrink: 0; position: sticky; top: 58px; align-self: flex-start; max-height: calc(100vh - 58px); display: flex; flex-direction: column; border-right: 1px solid var(--line); font-family: system-ui, "Microsoft YaHei", sans-serif; }
.toc.drawer { position: fixed; left: 0; top: 0; bottom: 0; z-index: 60; width: 280px; max-height: none; background: var(--panel); }
.toc-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 14px 8px; font-size: 12px; color: var(--muted); letter-spacing: .08em; }
.toc-scroll { overflow-y: auto; padding: 4px 8px 24px; }
.toc-ch { width: 100%; display: flex; align-items: center; gap: 8px; padding: 7px 8px; border-radius: 7px; font-size: 12.5px; color: var(--ink-soft); text-align: left; }
.toc-ch:hover { background: var(--accent-soft); }
.toc-ch.active { background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.toc-no { font-size: 10px; color: var(--muted); font-variant-numeric: tabular-nums; }
.toc-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.toc-count { font-size: 10px; color: var(--muted); }
.toc-pages { margin: 0 0 6px 18px; border-left: 1px solid var(--line); }
.toc-page { display: block; width: 100%; text-align: left; font-size: 11.5px; color: var(--muted); padding: 4px 8px 4px 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.toc-page:hover { color: var(--accent); }
.toc-page.active { color: var(--accent); }
.toc-page .dot { display: inline-block; width: 4px; height: 4px; border-radius: 50%; background: currentColor; margin-right: 7px; vertical-align: middle; opacity: .5; }
.toc-mask { position: fixed; inset: 0; background: rgba(0, 0, 0, .35); z-index: 55; }

.main { flex: 1; min-width: 0; padding: 0 28px 40px; }

/* 封面 */
.cover { max-width: 720px; margin: 0 auto; padding: 96px 0 72px; text-align: center; border-bottom: 1px solid var(--line); }
.cover-kicker { font-size: 12px; letter-spacing: .22em; color: var(--accent); text-transform: uppercase; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.cover-title { font-size: clamp(28px, 4.2vw, 44px); line-height: 1.32; margin: 22px 0 26px; font-weight: 700; }
.cover-rule { width: 64px; height: 3px; background: var(--accent); margin: 0 auto 26px; }
.cover-lead { font-size: calc(var(--fs) * 1.02); color: var(--ink-soft); line-height: 1.9; max-width: 34em; margin: 0 auto; }
.cover-meta { margin-top: 26px; font-size: 12px; color: var(--muted); font-family: system-ui, "Microsoft YaHei", sans-serif; }
.cover-start { margin-top: 30px; padding: 10px 26px; border-radius: 999px; background: var(--accent); color: #fff; font-size: 14px; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.cover-tip { margin-top: 16px; font-size: 11px; color: var(--muted); }

/* 章节 */
.chapter { max-width: 720px; margin: 0 auto; }
.ch-head { padding: 64px 0 12px; border-bottom: 1px solid var(--line); margin-bottom: 10px; }
.ch-kicker { font-size: 11px; letter-spacing: .2em; color: var(--accent); font-family: system-ui, "Microsoft YaHei", sans-serif; }
.ch-head h2 { font-size: clamp(22px, 3vw, 30px); line-height: 1.4; margin: 12px 0 10px; }
.ch-question { font-size: 13px; color: var(--muted); padding-left: 12px; border-left: 2px solid var(--accent); line-height: 1.8; }

.page { padding: 34px 0 38px; scroll-margin-top: 74px; border-bottom: 1px dashed var(--line); }
.page:last-child { border-bottom: none; }
.eyebrow { font-size: 11px; letter-spacing: .14em; color: var(--muted); font-family: system-ui, "Microsoft YaHei", sans-serif; }
.page-title { display: flex; align-items: baseline; gap: 10px; font-size: calc(var(--fs) * 1.3); line-height: 1.5; margin: 8px 0 12px; font-weight: 700; }
.seq { font-size: 11px; color: var(--accent); font-family: system-ui, "Microsoft YaHei", sans-serif; font-weight: 600; letter-spacing: .06em; }
.dek { font-size: calc(var(--fs) * .94); color: var(--ink-soft); line-height: 1.9; margin-bottom: 14px; font-style: italic; }
.para { font-size: var(--fs); line-height: 1.95; margin-bottom: 12px; text-align: justify; letter-spacing: .01em; }

.points { margin: 14px 0 16px; padding: 0; list-style: none; }
.points li { display: flex; gap: 10px; font-size: calc(var(--fs) * .93); line-height: 1.85; color: var(--ink-soft); margin-bottom: 9px; }
.points li.sub { margin-left: 22px; color: var(--muted); font-size: calc(var(--fs) * .87); }
.pt-dot { flex-shrink: 0; width: 6px; height: 6px; border-radius: 50%; background: var(--accent); margin-top: .72em; opacity: .7; }
.points li.sub .pt-dot { background: var(--muted); width: 4px; height: 4px; }

.cards { display: grid; gap: 10px; margin: 16px 0; }
.mini-card { border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; background: var(--panel); }
.mini-title { font-size: calc(var(--fs) * .88); font-weight: 700; margin-bottom: 5px; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.mini-desc { font-size: calc(var(--fs) * .82); line-height: 1.75; color: var(--muted); }

.compare { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 16px 0; }
.cmp-col { border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; background: var(--accent-soft); }
.cmp-col.right { background: var(--warm-soft); }
.cmp-title { font-size: calc(var(--fs) * .86); font-weight: 700; margin-bottom: 6px; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.cmp-col ul { list-style: disc; padding-left: 18px; }
.cmp-col li { font-size: calc(var(--fs) * .82); line-height: 1.8; color: var(--ink-soft); }

.metrics { display: flex; gap: 14px; margin: 16px 0; flex-wrap: wrap; }
.metric { flex: 1; min-width: 120px; border: 1px solid var(--line); border-radius: 10px; padding: 12px; text-align: center; background: var(--panel); }
.metric-val { font-size: calc(var(--fs) * 1.5); font-weight: 700; color: var(--accent); font-family: system-ui, "Microsoft YaHei", sans-serif; }
.metric-unit { font-size: 11px; margin-left: 2px; }
.metric-label { font-size: 11px; color: var(--muted); margin-top: 4px; }

.chart { margin: 18px 0; padding: 14px; border: 1px solid var(--line); border-radius: 10px; background: var(--panel); }
.chart-cap { font-size: 12px; color: var(--muted); margin-bottom: 10px; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.chart-row { display: grid; grid-template-columns: 84px 1fr 52px; align-items: center; gap: 8px; margin-bottom: 6px; }
.chart-label { font-size: 11.5px; color: var(--ink-soft); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chart-track { height: 8px; border-radius: 999px; background: var(--line); overflow: hidden; }
.chart-fill { display: block; height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--accent), color-mix(in srgb, var(--accent) 55%, #fff)); }
.chart-val { font-size: 11.5px; color: var(--muted); text-align: right; font-variant-numeric: tabular-nums; }
.chart-note { margin-top: 8px; font-size: 10.5px; color: var(--muted); }

.flow { list-style: none; padding: 0; margin: 16px 0; }
.flow-step { display: flex; gap: 12px; padding: 11px 0; border-bottom: 1px dashed var(--line); }
.flow-step:last-child { border-bottom: none; }
.flow-no { flex-shrink: 0; width: 22px; height: 22px; border-radius: 50%; background: var(--accent-soft); color: var(--accent); font-size: 11px; display: flex; align-items: center; justify-content: center; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.flow-title { font-size: calc(var(--fs) * .9); font-weight: 700; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.flow-desc { font-size: calc(var(--fs) * .82); color: var(--muted); line-height: 1.8; margin-top: 3px; }

.table-wrap { margin: 16px 0; overflow-x: auto; }
.table-wrap table { width: 100%; border-collapse: collapse; font-size: calc(var(--fs) * .78); }
.table-wrap td { border: 1px solid var(--line); padding: 7px 10px; line-height: 1.7; vertical-align: top; }
.table-wrap td.th { background: var(--accent-soft); font-weight: 700; }

.quote { margin: 18px 0; padding: 14px 18px; border-left: 3px solid var(--accent); font-size: calc(var(--fs) * 1.02); line-height: 1.9; color: var(--ink-soft); font-style: italic; }
.quote cite { display: block; margin-top: 8px; font-size: 11px; font-style: normal; color: var(--muted); }

.callout { margin: 16px 0; padding: 12px 15px; border-radius: 10px; line-height: 1.85; font-size: calc(var(--fs) * .86); }
.callout-label { font-size: 10.5px; letter-spacing: .1em; font-weight: 700; margin-bottom: 5px; font-family: system-ui, "Microsoft YaHei", sans-serif; opacity: .82; }
.callout.example { background: var(--warm-soft); border: 1px solid color-mix(in srgb, var(--warm) 24%, transparent); }
.callout.example .callout-label { color: var(--warm); }
.callout.takeaway { background: var(--accent-soft); border: 1px solid color-mix(in srgb, var(--accent) 22%, transparent); }
.callout.takeaway ul { list-style: disc; padding-left: 18px; }
.callout.notes { background: transparent; border: 1px dashed var(--line); color: var(--ink-soft); }
.callout.notes .callout-label { color: var(--muted); }

.plate { margin: 18px 0; }
.plate img { width: 100%; border-radius: 10px; border: 1px solid var(--line); background: #fff; }
.plate figcaption { margin-top: 6px; font-size: 10.5px; color: var(--muted); text-align: center; }
.risk { margin-top: 12px; font-size: 11.5px; color: var(--warm); background: var(--warm-soft); border-radius: 8px; padding: 8px 10px; }

.closing { max-width: 720px; margin: 0 auto; padding: 56px 0 20px; border-top: 1px solid var(--line); }
.closing h2 { font-size: clamp(20px, 2.6vw, 26px); margin-bottom: 20px; }
.closing-block { margin-bottom: 22px; }
.closing-title { font-size: 12px; letter-spacing: .12em; color: var(--accent); margin-bottom: 8px; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.closing-block ul { list-style: disc; padding-left: 20px; }
.closing-block li { font-size: calc(var(--fs) * .9); line-height: 1.95; color: var(--ink-soft); }

.pager { max-width: 720px; margin: 40px auto 0; display: flex; align-items: center; justify-content: space-between; gap: 12px; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.pager-btn { font-size: 13px; padding: 9px 18px; border-radius: 999px; border: 1px solid var(--line); background: var(--panel); color: var(--ink-soft); }
.pager-btn:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.pager-btn:disabled { opacity: .35; }
.pager-mid { font-size: 11.5px; color: var(--muted); font-variant-numeric: tabular-nums; }

.foot { max-width: 720px; margin: 28px auto 0; padding: 18px 0 8px; border-top: 1px solid var(--line); font-size: 10.5px; color: var(--muted); line-height: 1.9; text-align: center; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.foot-tip { display: block; }
.state { padding: 120px 0; text-align: center; color: var(--muted); font-size: 13px; }

/* 移动端：目录抽屉、工具栏换行 */
@media (max-width: 760px) {
  .bar { flex-wrap: wrap; padding: 8px 12px; }
  .bar-title h1 { max-width: 60vw; font-size: 13px; }
  .bar-progress, .bar-pct { display: none; }
  .main { padding: 0 18px 32px; }
  .cover { padding: 56px 0 44px; }
  .compare { grid-template-columns: 1fr; }
  .chart-row { grid-template-columns: 66px 1fr 44px; }
}
</style>
