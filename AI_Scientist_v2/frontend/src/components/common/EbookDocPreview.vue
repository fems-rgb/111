<template>
  <div class="docbook" :class="`theme-${theme}`" :style="{ '--fs': `${fontSize}px` }">
    <!-- 顶部：进度 + 字号 + 主题 -->
    <div class="db-bar">
      <div class="db-bar-left">
        <span class="db-badge">📄 电子书预览</span>
        <span class="db-title truncate" :title="displayTitle">{{ displayTitle }}</span>
      </div>
      <div class="db-bar-right">
        <div class="db-progress"><span :style="{ width: `${pct}%` }"></span></div>
        <span class="db-pct">{{ pct }}%</span>
        <button class="db-btn" @click="bumpFont(-1)" :disabled="fontSize <= 14">A－</button>
        <button class="db-btn" @click="bumpFont(1)" :disabled="fontSize >= 22">A＋</button>
        <button class="db-btn" @click="cycleTheme" :title="`主题：${themeLabel}`">{{ themeIcon }}</button>
        <button class="db-btn" :class="{ on: tocOpen }" @click="tocOpen = !tocOpen">☰ 目录</button>
        <button v-if="closable" class="db-btn" title="关闭预览" @click="$emit('close')">✕</button>
      </div>
    </div>

    <div class="db-scroll" ref="scrollEl" @scroll.passive="onScroll">
      <!-- 封面 -->
      <header class="db-cover">
        <p class="db-kicker">资料库 · 电子书</p>
        <h1>{{ displayTitle }}</h1>
        <div class="db-rule"></div>
        <p class="db-meta">{{ chapters.length }} 章 · {{ chars.toLocaleString() }} 字 · 约 {{ minutes }} 分钟</p>
      </header>

      <div class="db-layout">
        <!-- 目录 -->
        <aside v-if="tocOpen && chapters.length > 1" class="db-toc">
          <p class="db-toc-head">目录</p>
          <button v-for="(ch, i) in chapters" :key="i" class="db-toc-item" :class="{ active: activeCh === i }"
                  @click="goChapter(i)">
            <span class="db-toc-no">{{ pad(i + 1) }}</span>
            <span class="db-toc-name">{{ ch.title }}</span>
          </button>
        </aside>

        <main class="db-main">
          <article v-for="(ch, i) in chapters" :key="i" :id="`doc-ch-${i}`" class="db-chapter">
            <h2 v-if="chapters.length > 1">
              <span class="db-ch-no">{{ pad(i + 1) }}</span>{{ ch.title }}
            </h2>
            <template v-for="(b, bi) in ch.blocks" :key="bi">
              <h3 v-if="b.t === 'h3'" class="db-h3">{{ b.text }}</h3>
              <p v-else-if="b.t === 'p'" class="db-p">{{ b.text }}</p>
              <blockquote v-else-if="b.t === 'quote'" class="db-quote">{{ b.text }}</blockquote>
              <ul v-else-if="b.t === 'list'" class="db-list">
                <li v-for="(it, ii) in b.items" :key="ii">{{ it }}</li>
              </ul>
              <pre v-else-if="b.t === 'code'" class="db-code">{{ b.lines.join('\n') }}</pre>
            </template>
          </article>
          <p v-if="!chapters.length" class="db-empty">这份资料没有可阅读的正文。</p>
        </main>
      </div>

      <footer class="db-foot">
        {{ displayTitle }} · 全文 {{ chars.toLocaleString() }} 字
        <span class="db-foot-tip">字号与主题会记住；资料原文不受影响，标注请用「复制」或下载原文件</span>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

const props = defineProps<{ title: string; content: string; closable?: boolean }>()
defineEmits<{ close: [] }>()

const fontSize = ref(Number(localStorage.getItem('ebook_fs') || 18))
const theme = ref<'paper' | 'sepia' | 'night'>((localStorage.getItem('ebook_theme') as any) || 'paper')
const themeLabel = computed(() => ({ paper: '纸白', sepia: '护眼', night: '夜间' } as const)[theme.value])
const themeIcon = computed(() => ({ paper: '☀️', sepia: '🌿', night: '🌙' } as const)[theme.value])

const scrollEl = ref<HTMLElement | null>(null)
const pct = ref(0)
const activeCh = ref(0)
const tocOpen = ref(true)

type Block =
  | { t: 'h3' | 'p' | 'quote'; text: string }
  | { t: 'list'; items: string[] }
  | { t: 'code'; lines: string[] }
interface Chapter { title: string; blocks: Block[] }

const chars = computed(() => (props.content || '').length)
const minutes = computed(() => Math.max(1, Math.round(chars.value / 420)))
/** 封面/页眉用去掉扩展名的书名 */
const displayTitle = computed(() => (props.title || '未命名资料').replace(/\.(md|markdown|txt|json|csv|docx?|pdf|html?)$/i, '').trim() || '未命名资料')

/** 把纯文本 / Markdown / 从 Word 抽出的正文整理成「章 + 段落」 */
const chapters = computed<Chapter[]>(() => {
  const raw = (props.content || '').replace(/\r\n?/g, '\n')
  if (!raw.trim()) return []
  const lines = raw.split('\n')
  const out: Chapter[] = []
  let cur: Chapter = { title: displayTitle.value, blocks: [] }
  let buf = ''
  let inCode = false

  const last = () => cur.blocks[cur.blocks.length - 1]
  const flush = () => {
    if (buf.trim()) cur.blocks.push({ t: 'p', text: buf.trim() })
    buf = ''
  }
  const startChapter = (t: string) => {
    flush()
    if (cur.blocks.length) out.push(cur)
    cur = { title: t, blocks: [] }
  }
  const pushList = (item: string) => {
    const l = last()
    if (l && l.t === 'list') l.items.push(item)
    else cur.blocks.push({ t: 'list', items: [item] })
  }
  const pushCode = (line: string) => {
    const l = last()
    if (l && l.t === 'code') l.lines.push(line)
    else cur.blocks.push({ t: 'code', lines: [line] })
  }

  for (const rawLine of lines) {
    const line = rawLine.replace(/\s+$/, '')
    const t = line.trim()
    if (t.startsWith('```')) { flush(); inCode = !inCode; continue }
    if (inCode) { pushCode(rawLine); continue }
    if (!t) { flush(); continue }
    if (/^[-=_*]{3,}$/.test(t)) { flush(); continue }

    const md = /^(#{1,6})\s+(.*)$/.exec(t)
    if (md) {
      const text = md[2].trim()
      if (md[1].length <= 2) {
        // 一级标题常常就是文档标题，不再单列一章
        if (text && text !== displayTitle.value && text !== props.title) startChapter(text)
        else flush()
      } else {
        flush()
        cur.blocks.push({ t: 'h3', text })
      }
      continue
    }
    // 中文公文/论文常见章节写法
    if (/^第[一二三四五六七八九十百零\d]+[章节篇部]/.test(t) && t.length <= 80) { startChapter(t); continue }
    if (/^[一二三四五六七八九十]+、/.test(t) && t.length <= 60) { startChapter(t); continue }
    if (/^(\d+\.)+\d*\s+\S/.test(t) && t.length <= 60) { flush(); cur.blocks.push({ t: 'h3', text: t }); continue }
    if (/^[-*•·]\s+/.test(t)) { flush(); pushList(t.replace(/^[-*•·]\s+/, '')); continue }
    if (/^\d+[.、)]\s+/.test(t) && t.length <= 300) { flush(); pushList(t.replace(/^\d+[.、)]\s+/, '')); continue }
    if (t.startsWith('>')) { flush(); cur.blocks.push({ t: 'quote', text: t.replace(/^>\s?/, '') }); continue }
    // 普通段落：连续行合并，避免 Word 抽取的硬换行把一段拆碎
    buf += (buf ? ' ' : '') + t
  }
  flush()
  if (cur.blocks.length) out.push(cur)
  return out.length ? out : [{ title: displayTitle.value, blocks: [{ t: 'p', text: raw.trim() }] }]
})

function pad(n: number) { return String(n).padStart(2, '0') }

function bumpFont(d: number) {
  fontSize.value = Math.min(22, Math.max(14, fontSize.value + d))
  localStorage.setItem('ebook_fs', String(fontSize.value))
}
function cycleTheme() {
  theme.value = theme.value === 'paper' ? 'sepia' : theme.value === 'sepia' ? 'night' : 'paper'
  localStorage.setItem('ebook_theme', theme.value)
}
function goChapter(i: number) {
  const el = document.getElementById(`doc-ch-${i}`)
  const box = scrollEl.value
  if (!el || !box) return
  // 用相对滚动容器的位置，offsetTop 会参照更外层的定位祖先，导致跳转偏移
  const top = el.getBoundingClientRect().top - box.getBoundingClientRect().top + box.scrollTop
  box.scrollTo({ top: Math.max(0, top - 12), behavior: 'smooth' })
  activeCh.value = i
}

function onScroll() {
  const box = scrollEl.value
  if (!box) return
  const max = box.scrollHeight - box.clientHeight
  pct.value = max > 0 ? Math.min(100, Math.round((box.scrollTop / max) * 100)) : 100
  // 目录高亮：最后一个已经滚过顶部的章
  let idx = 0
  const boxTop = box.getBoundingClientRect().top
  chapters.value.forEach((_, i) => {
    const el = document.getElementById(`doc-ch-${i}`)
    if (el && el.getBoundingClientRect().top - boxTop <= 120) idx = i
  })
  activeCh.value = idx
}

onMounted(() => {
  if (window.innerWidth < 900) tocOpen.value = false
})
</script>

<style scoped>
.docbook {
  --bg: #fbfbf8;
  --panel: #ffffff;
  --ink: #1f2937;
  --ink-soft: #374151;
  --muted: #6b7280;
  --line: #e5e7eb;
  --accent: #4338ca;
  --accent-soft: #eef2ff;
  --fs: 18px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  color: var(--ink);
  font-family: Georgia, "Songti SC", "SimSun", "Noto Serif SC", serif;
}
.docbook.theme-sepia { --bg: #f6efe1; --panel: #fbf5e9; --ink: #3b3226; --ink-soft: #4b4133; --muted: #7c6f5c; --line: #e2d6c0; --accent: #8a5a1f; --accent-soft: #f3e7cf; }
.docbook.theme-night { --bg: #101319; --panel: #171b23; --ink: #e5e7eb; --ink-soft: #cbd5e1; --muted: #94a3b8; --line: #262c38; --accent: #a5b4fc; --accent-soft: #1e2433; }

.db-bar { flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 16px; border-bottom: 1px solid var(--line); background: var(--panel); font-family: system-ui, "Microsoft YaHei", sans-serif; }
.db-bar-left { display: flex; align-items: center; gap: 8px; min-width: 0; }
.db-badge { flex-shrink: 0; font-size: 11px; padding: 2px 8px; border-radius: 999px; background: var(--accent-soft); color: var(--accent); }
.db-title { font-size: 12.5px; color: var(--muted); max-width: 34vw; }
.db-bar-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.db-progress { width: 70px; height: 4px; border-radius: 999px; background: var(--line); overflow: hidden; }
.db-progress span { display: block; height: 100%; background: var(--accent); transition: width .25s; }
.db-pct { font-size: 10.5px; color: var(--muted); width: 28px; font-variant-numeric: tabular-nums; }
.db-btn { font-size: 11.5px; padding: 4px 8px; border-radius: 6px; border: 1px solid var(--line); background: transparent; color: var(--ink-soft); }
.db-btn:hover { border-color: var(--accent); color: var(--accent); }
.db-btn.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }
.db-btn:disabled { opacity: .4; }

.db-scroll { flex: 1; overflow-y: auto; }

.db-cover { max-width: 760px; margin: 0 auto; padding: 54px 32px 34px; text-align: center; border-bottom: 1px solid var(--line); }
.db-kicker { font-size: 11px; letter-spacing: .2em; color: var(--accent); font-family: system-ui, "Microsoft YaHei", sans-serif; }
.db-cover h1 { font-size: clamp(22px, 3vw, 32px); line-height: 1.4; margin: 16px 0 18px; }
.db-rule { width: 56px; height: 3px; background: var(--accent); margin: 0 auto 16px; }
.db-meta { font-size: 12px; color: var(--muted); font-family: system-ui, "Microsoft YaHei", sans-serif; }

.db-layout { display: flex; max-width: 1120px; margin: 0 auto; padding: 0 24px; }
.db-toc { width: 210px; flex-shrink: 0; padding: 22px 12px 40px 0; border-right: 1px solid var(--line); align-self: flex-start; position: sticky; top: 0; max-height: 100%; overflow-y: auto; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.db-toc-head { font-size: 11px; color: var(--muted); letter-spacing: .1em; padding: 0 8px 8px; }
.db-toc-item { display: flex; gap: 7px; width: 100%; text-align: left; font-size: 12px; color: var(--ink-soft); padding: 6px 8px; border-radius: 6px; line-height: 1.5; }
.db-toc-item:hover { background: var(--accent-soft); }
.db-toc-item.active { background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.db-toc-no { flex-shrink: 0; font-size: 10px; color: var(--muted); padding-top: 2px; }
.db-toc-name { overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }

.db-main { flex: 1; min-width: 0; max-width: 760px; padding: 10px 8px 40px 28px; }
.db-chapter { padding-top: 26px; }
.db-chapter h2 { display: flex; align-items: baseline; gap: 10px; font-size: calc(var(--fs) * 1.28); line-height: 1.5; margin: 18px 0 14px; padding-bottom: 8px; border-bottom: 1px solid var(--line); }
.db-ch-no { font-size: 11px; color: var(--accent); font-family: system-ui, "Microsoft YaHei", sans-serif; }
.db-h3 { font-size: calc(var(--fs) * 1.02); font-weight: 700; margin: 20px 0 8px; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.db-p { font-size: var(--fs); line-height: 1.95; margin-bottom: 12px; text-align: justify; }
.db-quote { margin: 14px 0; padding: 8px 16px; border-left: 3px solid var(--accent); color: var(--ink-soft); font-style: italic; font-size: calc(var(--fs) * .94); }
.db-list { margin: 8px 0 14px; padding-left: 22px; list-style: disc; }
.db-list li { font-size: calc(var(--fs) * .93); line-height: 1.9; color: var(--ink-soft); margin-bottom: 4px; }
.db-code { margin: 12px 0 16px; padding: 12px 14px; border-radius: 8px; background: var(--panel); border: 1px solid var(--line); font-family: Consolas, "Courier New", monospace; font-size: 12px; line-height: 1.7; overflow-x: auto; white-space: pre-wrap; }
.db-empty { padding: 40px 0; color: var(--muted); font-size: 13px; text-align: center; }

.db-foot { max-width: 760px; margin: 0 auto; padding: 20px 32px 40px; border-top: 1px solid var(--line); font-size: 10.5px; color: var(--muted); text-align: center; line-height: 1.9; font-family: system-ui, "Microsoft YaHei", sans-serif; }
.db-foot-tip { display: block; }

@media (max-width: 900px) {
  .db-toc { display: none; }
  .db-main { padding: 10px 18px 32px; }
  .db-cover { padding: 36px 20px 26px; }
  .db-pct, .db-progress { display: none; }
}
</style>
