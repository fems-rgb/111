<template>
  <div class="flex h-screen overflow-hidden">
    <AppSidebar />
    <div class="flex-1 flex flex-col overflow-hidden">
      <AppHeader />
      <main class="flex-1 overflow-y-auto p-6 bg-surface-50">
        <router-view :key="$route.fullPath" />
      </main>
    </div>
    <!-- SSE状态 -->
    <div class="fixed bottom-4 right-4 z-40">
      <div :class="['flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium shadow-lg', connected ? 'bg-green-600 text-white' : 'bg-red-600 text-white']">
        <span class="w-2 h-2 rounded-full bg-white animate-pulse"></span>
        {{ connected ? 'Live' : 'Reconnecting...' }}
      </div>
    </div>

    <!-- Toast 通知 -->
    <div class="fixed top-4 right-4 z-50 space-y-2">
      <transition-group name="slide-up">
        <div v-for="toast in (appStore as any).toasts" :key="toast.id"
             :class="['px-4 py-3 rounded-lg shadow-lg text-white text-sm', toast.type === 'error' ? 'bg-red-600' : toast.type === 'success' ? 'bg-green-600' : 'bg-primary-600']">
          {{ toast.message }}
        </div>
      </transition-group>
    </div>

    <!-- ===== 全局生成进度小窗（跨路由持久） ===== -->
    <Teleport to="body">
      <!-- 展开态 -->
      <div v-if="appStore.genTaskId && !appStore.genMinimized" class="fixed bottom-6 right-6 z-[60] w-80 animate-fade-in">
        <div class="relative bg-white rounded-2xl shadow-2xl border border-surface-200 p-5 space-y-4 text-center">
          <button @click="appStore.genMinimized = true"
                  class="absolute top-2 right-2 w-7 h-7 flex items-center justify-center rounded-full bg-surface-100 hover:bg-surface-200 text-surface-500 hover:text-surface-700 transition-colors z-10 text-sm"
                  title="收起(任务继续在后台运行)">−</button>

          <!-- 运行中 -->
          <template v-if="appStore.genStatus === 'running'">
            <div class="relative w-20 h-20 mx-auto">
              <svg class="animate-spin w-full h-full text-primary-200" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="8" />
              </svg>
              <svg class="absolute inset-0 animate-spin-slow w-full h-full text-primary-600" viewBox="0 0 100 100" style="animation-duration: 3s;">
                <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="8"
                        :stroke-dasharray="(283 * appStore.genProgress / 100) + ' ' + (283 - 283 * appStore.genProgress / 100)" stroke-linecap="round" style="transition: stroke-dasharray 0.5s ease" />
              </svg>
              <div class="absolute inset-0 flex items-center justify-center">
                <span class="text-lg font-bold text-primary-700">{{ appStore.genProgress }}%</span>
              </div>
            </div>
            <h3 class="text-xl font-bold text-surface-800">🚀 正在生成研究文档</h3>
            <p v-if="appStore.genTitle" class="text-sm text-surface-500 truncate px-4">{{ appStore.genTitle }}</p>
            <div v-if="appStore.genProgress > 0" class="w-full bg-surface-100 rounded-full h-3 overflow-hidden">
              <div class="h-full bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-700 ease-out rounded-full"
                   :style="{ width: appStore.genProgress + '%' }"></div>
            </div>
            <p class="text-xs text-surface-400">{{ appStore.genProgress > 0 ? 'AI 正在分析题目并撰写报告，请稍候...' : '🚀 任务已提交，正在初始化流水线...' }}</p>
          </template>

          <!-- 完成 -->
          <template v-else-if="appStore.genStatus === 'completed'">
            <div class="w-20 h-20 mx-auto bg-green-100 rounded-full flex items-center justify-center">
              <svg class="w-10 h-10 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-green-700">✅ 文档生成完成！</h3>
            <p v-if="appStore.genTitle" class="text-sm text-surface-500 truncate px-4">{{ appStore.genTitle }}</p>
            <div class="flex gap-3 justify-center pt-2">
              <button @click="appStore.closeGenProgress()"
                      class="px-5 py-2.5 rounded-xl text-sm font-medium bg-green-600 text-white hover:bg-green-700 transition-colors shadow-lg shadow-green-200">
                📄 查看文档
              </button>
            </div>
            <button @click="appStore.closeGenProgress()" class="text-xs text-surface-400 hover:text-surface-600 mt-2">关闭</button>
          </template>

          <!-- 失败 -->
          <template v-else-if="appStore.genStatus === 'failed'">
            <div class="w-20 h-20 mx-auto bg-red-100 rounded-full flex items-center justify-center">
              <svg class="w-10 h-10 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-red-700">❌ 生成失败</h3>
            <p class="text-sm text-surface-500">请查看任务详情了解错误原因</p>
            <button @click="appStore.closeGenProgress()"
                    class="mt-2 px-5 py-2.5 rounded-xl text-sm font-medium bg-surface-100 text-surface-700 hover:bg-surface-200 transition-colors">
              关闭
            </button>
          </template>
        </div>
      </div>

      <!-- 收起态 -->
      <div v-if="appStore.genTaskId && appStore.genMinimized"
           class="fixed bottom-6 right-6 z-[60] w-72 bg-white rounded-xl shadow-lg border border-surface-200 px-4 py-3 flex items-center gap-3 cursor-pointer hover:shadow-xl transition-shadow animate-fade-in"
           @click="appStore.genMinimized = false">
        <svg class="animate-spin w-5 h-5 text-primary-600 flex-shrink-0" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="10"
                  :stroke-dasharray="(283 * appStore.genProgress / 100) + ' ' + (283 - 283 * appStore.genProgress / 100)" stroke-linecap="round" />
        </svg>
        <div class="flex-1 min-w-0">
          <p class="text-xs font-semibold text-surface-700 truncate">{{ appStore.genTitle || '生成中...' }}</p>
          <p class="text-[10px] text-surface-400">{{ appStore.genProgress }}% · 点击展开</p>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
import { useAppStore } from '@/stores/app'
import { useSSE } from '@/composables/useSSE'
const appStore = useAppStore()
const { connected, connect } = useSSE()

import { onMounted } from 'vue'
onMounted(() => { connect() })
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(-12px); }
</style>
