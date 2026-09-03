import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { Project, AgentTask, ProjectStats } from '@/types'
import { projectApi } from '@/api/modules/project'

const STORAGE_KEY = 'ai_scientist_project_store'
function loadFromStorage(): Record<string, any> { try { const raw = localStorage.getItem(STORAGE_KEY); return raw ? JSON.parse(raw) : {} } catch { return {} } }
function saveToStorage(data: Record<string, any>) { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)) } catch {} }

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const tasks = ref<AgentTask[]>([])
  const stats = ref<ProjectStats>({ total: 0, running: 0, completed: 0, task_count: 0, active_pipelines: 0, trace_count: 0 })
  const loading = ref(false)

  const cached = loadFromStorage()
  if (cached.currentProjectId) {
    const _cachedId = cached.currentProjectId as number
    setTimeout(async () => { if (!currentProject.value && projects.value.length > 0) { const found = projects.value.find(p => p.id === _cachedId); if (found) currentProject.value = found } }, 100)
  }
  watch(currentProject, (proj) => { saveToStorage({ currentProjectId: proj?.id ?? null }) })

  async function fetchProjects(params?: { status?: string; workspace?: string }) {
    loading.value = true
    try {
      const res = await projectApi.list(params)
      projects.value = res.data
    } catch (e) {
      console.error('fetchProjects failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id: number) {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 15000)
    try {
      const res = await projectApi.get(id)
      currentProject.value = res.data
    } finally {
      clearTimeout(timeout)
    }
  }

  async function fetchTasks(projectId: number) {
    try {
      const res = await projectApi.getTasks(projectId)
      tasks.value = res.data
    } catch (e) {
      console.error('fetchTasks failed:', e)
    }
  }

  async function fetchStats(workspace?: string) {
    try {
      const res = await projectApi.getStats(workspace ? { workspace } : undefined)
      stats.value = { ...stats.value, ...res.data }
    } catch (e) {
      console.error('fetchStats failed:', e)
    }
  }

  async function createProject(data: any) { const res = await projectApi.create(data); projects.value.unshift(res.data); return res.data }
  async function startProject(id: number, pipeline?: string[]) { return await projectApi.start(id, pipeline) }
  async function deleteProject(id: number) { await projectApi.delete(id); projects.value = projects.value.filter(p => p.id !== id); if (currentProject.value?.id === id) currentProject.value = null }
  async function shareProject(id: number, targetWorkspace: string) { return await projectApi.share(id, targetWorkspace) }
  async function unshareProject(id: number, targetWorkspace: string) { return await projectApi.unshare(id, targetWorkspace) }
  function setCurrentProject(project: Project | null) { currentProject.value = project }

  return { projects, currentProject, tasks, stats, loading, fetchProjects, fetchProject, fetchTasks, fetchStats, createProject, startProject, deleteProject, setCurrentProject, shareProject, unshareProject }
})
