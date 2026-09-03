<template>
  <div class="prose prose-sm max-w-none" v-html="renderedContent"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps<{ content: string }>()

function renderLatex(tex: string, displayMode: boolean): string {
  try {
    return katex.renderToString(tex, {
      displayMode,
      throwOnError: false,
      trust: true,
      strict: false
    })
  } catch (e) {
    return `<span class="text-red-500 font-mono text-xs" title="${(e as Error).message}">${tex}</span>`
  }
}

// markdown-it 插件：行内 $...$ 和块级 $$...$$
function latexPlugin(md: any) {
  // 块级 $$...$$
  md.block.ruler.after('blockquote', 'katex_block', (state: any, startLine: number, endLine: number) => {
    const startPos = state.bMarks[startLine] + state.tShift[startLine]
    const maxPos = state.eMarks[startLine]
    if (startPos + 2 > maxPos || state.src.slice(startPos, startPos + 2) !== '$$') return false
    let nextLine = startLine
    let hasEnding = false
    while (++nextLine < endLine) {
      const ls = state.bMarks[nextLine] + state.tShift[nextLine]
      const le = state.eMarks[nextLine]
      if (state.src.slice(ls, le).trim() === '$$') { hasEnding = true; break }
    }
    state.line = nextLine + (hasEnding ? 1 : 0)
    const token = state.push('katex_block', '', 0)
    token.content = state.src.slice(state.bMarks[startLine + 1], state.bMarks[nextLine]).trim()
    token.map = [startLine, state.line]
    return true
  })
  md.renderer.rules.katex_block = (tokens: any[], idx: number) =>
    `<div class="katex-display my-4 overflow-x-auto py-3 px-4 bg-surface-50 rounded-lg">${renderLatex(tokens[idx].content, true)}</div>`

  // 行内 $...$
  md.inline.ruler.after('escape', 'katex_inline', (state: any, silent: boolean) => {
    if (state.src[state.pos] !== '$' || state.src[state.pos + 1] === '$') return false
    const start = state.pos + 1
    let end = start
    while (end < state.posMax) {
      if (state.src[end] === '$' && state.src[end - 1] !== '\\') break
      end++
    }
    if (end >= state.posMax || end === start) return false
    if (!silent) {
      const token = state.push('katex_inline', '', 0)
      token.content = state.src.slice(start, end)
    }
    state.pos = end + 1
    return true
  })
  md.renderer.rules.katex_inline = (tokens: any[], idx: number) =>
    renderLatex(tokens[idx].content, false)
}

const md = new MarkdownIt({ html: true, linkify: true, typographer: true, breaks: true })
md.use(latexPlugin)

const renderedContent = computed(() => {
  if (!props.content) return ''
  try {
    return md.render(props.content)
  } catch {
    return props.content
  }
})
</script>

<style>
/* 保留原有 prose 样式 */
.prose h1 { @apply text-2xl font-bold mt-6 mb-4; }
.prose h2 { @apply text-xl font-semibold mt-5 mb-3; }
.prose h3 { @apply text-lg font-medium mt-4 mb-2; }
.prose p { @apply mb-3 leading-relaxed; }
.prose ul, .prose ol { @apply ml-6 mb-3; }
.prose li { @apply mb-1; }
.prose code { @apply bg-surface-100 px-1.5 py-0.5 rounded text-sm font-mono text-primary-700; }
.prose pre { @apply bg-surface-800 text-surface-100 p-4 rounded-lg overflow-x-auto mb-4; }
.prose pre code { @apply bg-transparent text-surface-100 p-0; }
.prose blockquote { @apply border-l-4 border-primary-300 pl-4 italic text-surface-600 my-4; }
.prose table { @apply w-full border-collapse mb-4; }
.prose th { @apply bg-surface-100 px-3 py-2 text-left font-medium border border-surface-200; }
.prose td { @apply px-3 py-2 border border-surface-200; }
/* KaTeX 额外样式 */
.prose .katex-display { @apply my-4 overflow-x-auto; }
.prose .katex { font-size: 1em; }
</style>