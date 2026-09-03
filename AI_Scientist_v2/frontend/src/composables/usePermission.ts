import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

export function usePermission() {
  const authStore = useAuthStore()
  const isAdmin = computed(() => authStore.user?.role === 'admin')
  const isTeacher = computed(() => authStore.user?.role === 'teacher')
  const canManageUsers = computed(() => isAdmin.value)
  const canViewAllProjects = computed(() => isAdmin.value || isTeacher.value)
  return { isAdmin, isTeacher, canManageUsers, canViewAllProjects }
}