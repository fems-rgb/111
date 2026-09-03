<template>
  <div class="space-y-6 animate-fade-in">
    <!-- 系统统计 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="card text-center">
        <p class="text-3xl font-bold text-primary-600">{{ systemStats.user_count || 0 }}</p>
        <p class="text-sm text-surface-500">总用户数</p>
      </div>
      <div class="card text-center">
        <p class="text-3xl font-bold text-green-600">{{ systemStats.project_count || 0 }}</p>
        <p class="text-sm text-surface-500">总项目数</p>
      </div>
      <div class="card text-center">
        <p class="text-3xl font-bold text-purple-600">¥{{ systemStats.cost_summary?.total_cost_yuan?.toFixed(2) || '0.00' }}</p>
        <p class="text-sm text-surface-500">总API成本</p>
      </div>
      <div class="card text-center">
        <p class="text-3xl font-bold text-red-600">{{ systemStats.prompt_guard?.blocked_count || 0 }}</p>
        <p class="text-sm text-surface-500">注入拦截次数</p>
      </div>
    </div>

    <!-- 用户管理 -->
    <div class="card">
      <h2 class="text-lg font-semibold mb-4">👥 用户管理</h2>
      <div v-if="users.length === 0" class="text-center py-8 text-surface-400">暂无用户</div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-surface-200">
              <th class="text-left py-3 px-3 font-medium">用户名</th>
              <th class="text-left py-3 px-3 font-medium">邮箱</th>
              <th class="text-left py-3 px-3 font-medium">角色</th>
              <th class="text-left py-3 px-3 font-medium">机构</th>
              <th class="text-left py-3 px-3 font-medium">状态</th>
              <th class="text-left py-3 px-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id" class="border-b border-surface-100 hover:bg-surface-50">
              <td class="py-3 px-3 font-medium">{{ u.username }}</td>
              <td class="py-3 px-3 text-surface-500">{{ u.email }}</td>
              <td class="py-3 px-3"><span class="badge-info">{{ u.role }}</span></td>
              <td class="py-3 px-3 text-surface-500">{{ u.institution || '-' }}</td>
              <td class="py-3 px-3">
                <span :class="// @ts-ignore
                  u.is_active !== false ? 'badge-success' : 'badge-error'">
                  {{ // @ts-ignore
                  u.is_active !== false ? '正常' : '禁用' }}
                </span>
              </td>
              <td class="py-3 px-3">
                <button @click="toggleUser(u.id)" class="text-primary-600 hover:underline text-xs">
                  {{ // @ts-ignore
                  u.is_active !== false ? '禁用' : '启用' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/modules/admin'
import { useAppStore } from '@/stores/app'
import type { User } from '@/types'

const appStore = useAppStore()
const systemStats = ref<any>({})
const users = ref<User[]>([])

async function fetchData() {
  try {
    const [statsRes, usersRes] = await Promise.all([adminApi.getStats(), adminApi.getUsers()])
    systemStats.value = statsRes.data
    users.value = usersRes.data
  } catch {}
}

async function toggleUser(userId: number) {
  try {
    await adminApi.toggleUser(userId)
    appStore.showToast('操作成功', 'success')
    await fetchData()
  } catch {
    appStore.showToast('操作失败', 'error')
  }
}

onMounted(fetchData)
</script>