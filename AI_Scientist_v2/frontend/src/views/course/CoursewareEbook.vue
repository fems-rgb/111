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
        <button class="btn" :class="{ on: showHlPanel }" @click="showHlPanel = !showHlPanel" title="荧光笔标注列表">🖊 标注{{ highlights.length ? ` ${highlights.length}` : '' }}</button>
        <button class="btn" :class="{ on: penOn }" @click="togglePen" title="手绘圈画：在书页上直接画线/圈重点">✏️ 圈画</button>
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

              <!-- 手绘圈画层（笔迹按页存，随书保存） -->
              <svg v-if="penOn || strokes[String(p.slide_index)]?.length" class="ink" :class="{ drawing: penOn }"
                   viewBox="0 0 100 100" preserveAspectRatio="none"
                   @pointerdown="penDown($event, p.slide_index)" @pointermove="penMove"
                   @pointerup="penUp" @pointerleave="penUp" @pointercancel="penUp">
                <polyline v-for="(s, si) in (strokes[String(p.slide_index)] || [])" :key="si"
                          :points="s.points.map((pt) => pt.join(',')).join(' ')"
                          fill="none" :stroke="s.color" :stroke-width="s.width"
                          stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke" />
              </svg>
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
            <span class="foot-tip">选中文字可荧光笔标注 · ✏️ 圈画可手绘 · 快捷键 ← → 翻节</span>
          </footer>
        </template>
      </main>
    </div>

    <!-- 标注列表（只有荧光笔结果） -->
    <aside v-if="showHlPanel" class="eb-hl-panel">
      <div class="eb-hl-head">
        <p>标注 · {{ highlights.length }}</p>
        <button @click="showHlPanel = false">✕</button>
      </div>
      <div class="eb-hl-list">
        <p v-if="!highlights.length" class="eb-hl-empty">在正文里选中文字，会弹出荧光笔工具条；高亮会随书保存。</p>
        <div v-for="h in sortedHighlights" :key="h.id" class="eb-hl-item">
          <span class="eb-hl-dot" :style="{ background: hlBg(h.color) }"></span>
          <button class="eb-hl-text" :title="`跳到第 ${h.page + 1} 页`" @click="jumpToHl(h)">{{ h.text }}</button>
          <button class="eb-hl-del" title="删除这条标注" @click="removeHl(h.id)">×</button>
        </div>
      </div>
      <button v-if="highlights.length" class="eb-hl-clear" @click="clearHl">清除全部标注</button>
    </aside>

    <!-- 圈画工具条 -->
    <div v-if="penOn" class="eb-pen-bar">
      <span class="eb-pen-label">圈画</span>
      <button v-for="c in PEN_COLORS" :key="c" class="eb-pen-color" :class="{ on: penColor === c }"
              :style="{ background: c }" @click="penColor = c"></button>
      <button class="eb-pen-btn" :class="{ on: penWidth === 2.5 }" @click="penWidth = 2.5">细</button>
      <button class="eb-pen-btn" :class="{ on: penWidth === 5 }" @click="penWidth = 5">粗</button>
      <button class="eb-pen-btn" @click="undoInk">撤销</button>
      <button class="eb-pen-btn" @click="clearInk">清本页</button>
      <button class="eb-pen-btn primary" @click="penOn = false">完成</button>
    </div>

    <!-- 选中文字后的荧光笔菜单（渲染到 body，避免被书页层叠上下文裁剪） -->
    <Teleport to="body">
      <div v-if="hlMenu.show" class="eb-hl-menu" :style="{ left: `${hlMenu.x}px`, top: `${hlMenu.y}px` }"
           @mousedown.prevent>
        <span class="eb-hl-menu-label">荧光笔</span>
        <button v-for="c in HL_COLORS" :key="c.key" class="eb-hl-swatch" :style="{ background: c.bg }"
                :title="c.label" @click="addHighlight(c.key)"></button>
        <button class="eb-hl-menu-x" @click="closeHlMenu">✕</button>
      </div>
    </Teleport>
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

// ── 圈画：荧光笔标注 + 手绘 ────────────────────────────────
type HlColor = 'yellow' | 'green' | 'pink' | 'blue'
interface Hl { id: string; page: number; start: number; end: number; color: HlColor; text: string; at: number }
interface InkStroke { color: string; width: number; points: [number, number][] }

const HL_COLORS: { key: HlColor; label: string; bg: string }[] = [
  { key: 'yellow', label: '黄色荧光笔', bg: '#fde68a' },
  { key: 'green', label: '绿色荧光笔', bg: '#bbf7d0' },
  { key: 'pink', label: '粉色荧光笔', bg: '#fbcfe8' },
  { key: 'blue', label: '蓝色荧光笔', bg: '#bfdbfe' },
]
const PEN_COLORS = ['#e11d48', '#2563eb', '#059669']

const highlights = ref<Hl[]>([])
const showHlPanel = ref(false)
const hlMenu = ref({ show: false, x: 0, y: 0, page: 0, start: 0, end: 0, text: '' })
const penOn = ref(false)
const penColor = ref(PEN_COLORS[0])
const penWidth = ref(2.5)
const strokes = ref<Record<string, InkStroke[]>>({})
let drawing: { key: string; stroke: InkStroke } | null = null

const sortedHighlights = computed(() =>
  [...highlights.value].sort((a, b) => a.page - b.page || a.start - b.start))

function hlBg(c: HlColor) { return HL_COLORS.find((x) => x.key === c)?.bg || '#fde68a' }

function saveHl() { localStorage.setItem(`ebook_hl_${cwId.value}`, JSON.stringify(highlights.value)) }
function saveInk() { localStorage.setItem(`ebook_ink_${cwId.value}`, JSON.stringify(strokes.value)) }

/** 页内字符偏移：把 Range 的两端换算成相对页面文本的序号，重渲染后还能复原 */
function offsetWithin(root: HTMLElement, node: Node, offset: number) {
  try {
    const r = document.createRange()
    r.selectNodeContents(root)
    r.setEnd(node, offset)
    return r.toString().length
  } catch { return 0 }
}

function rangeFromOffsets(root: HTMLElement, start: number, end: number): Range | null {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  let pos = 0
  let startNode: Text | null = null
  let endNode: Text | null = null
  let startOffset = 0
  let endOffset = 0
  let n: Node | null
  while ((n = walker.nextNode())) {
    const t = n as Text
    if (!startNode && pos + t.data.length >= start) {
      startNode = t
      startOffset = start - pos
    }
    if (pos + t.data.length >= end) {
      endNode = t
      endOffset = end - pos
      break
    }
    pos += t.data.length
  }
  if (!startNode || !endNode) return null
  const r = document.createRange()
  r.setStart(startNode, Math.max(0, Math.min(startOffset, startNode.data.length)))
  r.setEnd(endNode, Math.max(0, Math.min(endOffset, endNode.data.length)))
  return r
}

/** 用 CSS Custom Highlight 上色：不改 DOM，字号/主题/插图切换后范围依然有效 */
function applyHighlights() {
  const cssAny = window.CSS as any
  if (!cssAny?.highlights || typeof (window as any).Highlight === 'undefined') return
  for (const c of HL_COLORS) cssAny.highlights.delete(`eb-${c.key}`)
  for (const c of HL_COLORS) {
    const items = highlights.value.filter((h) => h.color === c.key)
    if (!items.length) continue
    const hi = new (window as any).Highlight()
    for (const h of items) {
      const el = document.getElementById(`pg-${h.page}`)
      const r = el ? rangeFromOffsets(el, h.start, h.end) : null
      if (r) hi.add(r)
    }
    cssAny.highlights.set(`eb-${c.key}`, hi)
  }
}

function onTextSelect() {
  if (penOn.value) return
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0 || sel.isCollapsed) { hlMenu.value.show = false; return }
  const range = sel.getRangeAt(0)
  const startEl = (range.startContainer.nodeType === 1 ? range.startContainer as Element : range.startContainer.parentElement)
  const pageEl = startEl?.closest('[data-page]') as HTMLElement | null
  if (!pageEl) { hlMenu.value.show = false; return }
  const endEl = (range.endContainer.nodeType === 1 ? range.endContainer as Element : range.endContainer.parentElement)
  if (endEl?.closest('[data-page]') !== pageEl) { hlMenu.value.show = false; return }
  const start = offsetWithin(pageEl, range.startContainer, range.startOffset)
  const end = offsetWithin(pageEl, range.endContainer, range.endOffset)
  if (end - start < 2) { hlMenu.value.show = false; return }
  const rect = range.getBoundingClientRect()
  hlMenu.value = {
    show: true,
    x: Math.min(Math.max(12, rect.left + rect.width / 2 - 100), window.innerWidth - 220),
    y: Math.min(rect.bottom + 10, window.innerHeight - 56),
    page: Number(pageEl.dataset.page),
    start,
    end,
    text: sel.toString().trim().replace(/\s+/g, ' ').slice(0, 160),
  }
}

function addHighlight(color: HlColor) {
  const m = hlMenu.value
  if (!m.show) return
  highlights.value.push({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    page: m.page, start: m.start, end: m.end, color, text: m.text, at: Date.now(),
  })
  saveHl()
  applyHighlights()
  closeHlMenu()
}

function closeHlMenu() {
  hlMenu.value.show = false
  window.getSelection()?.removeAllRanges()
}

function removeHl(id: string) {
  highlights.value = highlights.value.filter((h) => h.id !== id)
  saveHl()
  applyHighlights()
}

function clearHl() {
  if (!confirm('清除本书全部荧光笔标注？')) return
  highlights.value = []
  saveHl()
  applyHighlights()
}

function jumpToHl(h: Hl) {
  scrollTo(`pg-${h.page}`)
  if (!wide.value) showHlPanel.value = false
}

function togglePen() {
  penOn.value = !penOn.value
  hlMenu.value.show = false
  if (penOn.value) showHlPanel.value = false
}

function penPoint(e: PointerEvent, el: Element): [number, number] {
  const r = el.getBoundingClientRect()
  const x = r.width ? ((e.clientX - r.left) / r.width) * 100 : 0
  const y = r.height ? ((e.clientY - r.top) / r.height) * 100 : 0
  return [Math.round(Math.max(0, Math.min(100, x)) * 10) / 10, Math.round(Math.max(0, Math.min(100, y)) * 10) / 10]
}

function penDown(e: PointerEvent, page: number) {
  if (!penOn.value) return
  const svg = e.currentTarget as Element
  const pageEl = svg.closest('.page') as HTMLElement | null
  if (!pageEl) return
  ;(svg as any).setPointerCapture?.(e.pointerId)
  const stroke: InkStroke = { color: penColor.value, width: penWidth.value, points: [penPoint(e, pageEl)] }
  const key = String(page)
  if (!strokes.value[key]) strokes.value[key] = []
  strokes.value[key].push(stroke)
  drawing = { key, stroke }
}

function penMove(e: PointerEvent) {
  if (!drawing) return
  const svg = e.currentTarget as Element
  const pageEl = svg.closest('.page') as HTMLElement | null
  if (!pageEl) return
  drawing.stroke.points.push(penPoint(e, pageEl))
}

function penUp() {
  if (!drawing) return
  const list = strokes.value[drawing.key] || []
  // 点一下不画线，避免误触留下小圆点
  if (drawing.stroke.points.length < 2) {
    const i = list.indexOf(drawing.stroke)
    if (i >= 0) list.splice(i, 1)
  }
  drawing = null
  saveInk()
}

function undoInk() {
  const key = String(activePage.value)
  const list = strokes.value[key] || []
  if (!list.length) return
  list.pop()
  if (!list.length) delete strokes.value[key]
  saveInk()
}

function clearInk() {
  const key = String(activePage.value)
  if (!strokes.value[key]?.length) return
  delete strokes.value[key]
  saveInk()
}

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
function hideHlMenu() { if (hlMenu.value.show) hlMenu.value.show = false }

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
  // 插图会插入 <figure>，重算一遍标注范围
  nextTick(applyHighlights)
}
function toggleNotes() {
  showNotes.value = !showNotes.value
  nextTick(applyHighlights)
}
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
  window.addEventListener('mouseup', onTextSelect)
  window.addEventListener('scroll', hideHlMenu, { passive: true })
  try {
    meta.value = await coursewareApi.detail(cwId.value).then((r) => r.data)
    if (meta.value?.is_teacher) showNotes.value = localStorage.getItem('ebook_notes') === '1'
  } catch {
    meta.value = null
  } finally {
    loading.value = false
  }
  // 标注与笔迹都是本书本地保存，换设备不会同步
  try {
    highlights.value = JSON.parse(localStorage.getItem(`ebook_hl_${cwId.value}`) || '[]')
    strokes.value = JSON.parse(localStorage.getItem(`ebook_ink_${cwId.value}`) || '{}')
  } catch { highlights.value = []; strokes.value = {} }
  await nextTick()
  observePages()
  applyHighlights()
  // 恢复上次阅读位置
  const at = Number(localStorage.getItem(`ebook_at_${cwId.value}`) || 0)
  if (at > 0) setTimeout(() => scrollTo(`pg-${at}`), 120)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  window.removeEventListener('resize', onResize)
  window.removeEventListener('mouseup', onTextSelect)
  window.removeEventListener('scroll', hideHlMenu)
  observer?.disconnect()
  const cssAny = window.CSS as any
  if (cssAny?.highlights) for (const c of HL_COLORS) cssAny.highlights.delete(`eb-${c.key}`)
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

.page { position: relative; padding: 34px 0 38px; scroll-margin-top: 74px; border-bottom: 1px dashed var(--line); }
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

<!-- 圈画/标注必须放在全局样式里：Teleport 到 body 的菜单不受 scoped 约束，
     荧光笔用 CSS Custom Highlight 上色（不改 DOM，重渲染/切字号也不会丢） -->
<style>
::highlight(eb-yellow) { background-color: #fde68a; }
::highlight(eb-green) { background-color: #bbf7d0; }
::highlight(eb-pink) { background-color: #fbcfe8; }
::highlight(eb-blue) { background-color: #bfdbfe; }

.ink { position: absolute; inset: 0; z-index: 3; pointer-events: none; overflow: visible; }
.ink.drawing { pointer-events: auto; cursor: crosshair; touch-action: none; }
.page:has(.ink.drawing) { user-select: none; }

.eb-hl-menu {
  position: fixed; z-index: 90; display: flex; align-items: center; gap: 6px;
  padding: 7px 8px; border-radius: 10px; background: #fff;
  border: 1px solid #e5e7eb; box-shadow: 0 10px 30px rgba(15, 23, 42, .18);
  font-family: system-ui, "Microsoft YaHei", sans-serif;
}
.eb-hl-menu-label { font-size: 11px; color: #6b7280; margin-right: 2px; }
.eb-hl-swatch { width: 20px; height: 20px; border-radius: 50%; border: 2px solid transparent; cursor: pointer; }
.eb-hl-swatch:hover { transform: scale(1.12); }
.eb-hl-menu-x { font-size: 12px; color: #9ca3af; padding: 2px 4px; cursor: pointer; }

.eb-hl-panel {
  position: fixed; right: 16px; top: 64px; bottom: 16px; width: 300px; z-index: 60;
  display: flex; flex-direction: column; background: #fff; border: 1px solid #e5e7eb;
  border-radius: 12px; box-shadow: 0 10px 30px rgba(15, 23, 42, .15);
  font-family: system-ui, "Microsoft YaHei", sans-serif;
}
.eb-hl-head { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; border-bottom: 1px solid #e5e7eb; font-size: 12px; font-weight: 600; color: #374151; }
.eb-hl-list { flex: 1; overflow-y: auto; padding: 8px; }
.eb-hl-item { display: flex; align-items: flex-start; gap: 6px; padding: 6px; border-radius: 8px; }
.eb-hl-item:hover { background: #f9fafb; }
.eb-hl-dot { width: 4px; align-self: stretch; border-radius: 999px; flex-shrink: 0; }
.eb-hl-text { flex: 1; text-align: left; font-size: 12px; line-height: 1.6; color: #374151; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.eb-hl-del { color: #9ca3af; font-size: 14px; padding: 0 4px; flex-shrink: 0; }
.eb-hl-del:hover { color: #dc2626; }
.eb-hl-clear { margin: 8px 12px 12px; padding: 7px; border-radius: 8px; background: #fef2f2; color: #b91c1c; font-size: 12px; }
.eb-hl-empty { font-size: 12px; color: #9ca3af; line-height: 1.8; padding: 12px; }

.eb-pen-bar {
  position: fixed; left: 50%; bottom: 18px; transform: translateX(-50%); z-index: 70;
  display: flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 999px;
  background: #111827; color: #f9fafb; box-shadow: 0 12px 32px rgba(0, 0, 0, .28);
  font-family: system-ui, "Microsoft YaHei", sans-serif;
}
.eb-pen-label { font-size: 11px; color: #9ca3af; }
.eb-pen-color { width: 18px; height: 18px; border-radius: 50%; border: 2px solid transparent; cursor: pointer; }
.eb-pen-color.on { border-color: #fff; box-shadow: 0 0 0 2px rgba(255, 255, 255, .25); }
.eb-pen-btn { font-size: 11px; padding: 4px 9px; border-radius: 999px; background: #1f2937; color: #e5e7eb; cursor: pointer; }
.eb-pen-btn:hover { background: #374151; }
.eb-pen-btn.on { background: #4b5563; color: #fff; }
.eb-pen-btn.primary { background: #4f46e5; color: #fff; }

@media (max-width: 760px) {
  .eb-hl-panel { left: 12px; right: 12px; width: auto; top: auto; height: 45vh; }
  .eb-pen-bar { gap: 6px; padding: 7px 10px; }
}
</style>
