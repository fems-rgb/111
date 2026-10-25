import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'Login', component: () => import('@/views/auth/LoginView.vue'), meta: { guest: true } },
    {
      path: '/', component: () => import('@/components/layout/AppLayout.vue'), meta: { requiresAuth: true },
      children: [
        { path: '', name: 'Dashboard', component: () => import('@/views/workspace/DashboardView.vue') },
        { path: 'project/:id', name: 'ProjectDetail', component: () => import('@/views/workspace/ProjectDetail.vue') },
        { path: 'agents', name: 'Agents', component: () => import('@/views/agents/AgentPlayground.vue') },
        { path: 'chat', name: 'Chat', component: () => import('@/views/chat/ChatView.vue') },
        { path: 'traces', name: 'Traces', component: () => import('@/views/observability/TraceView.vue') },
        { path: 'cost', name: 'Cost', component: () => import('@/views/observability/CostView.vue') },
        // === 新增：科研闭环核心模块（对标 WorkBuddy）===
        { path: 'knowledge', name: 'KnowledgeBase', component: () => import('@/views/knowledge/KnowledgeView.vue'), meta: { title: '资料库' } },
        { path: 'skills', name: 'SkillMarket', component: () => import('@/views/skills/SkillMarketView.vue'), meta: { title: '技能市场' } },
        { path: 'automation', name: 'Automation', component: () => import('@/views/automation/AutomationView.vue'), meta: { title: '自动化流水线' } },
        { path: 'questions', name: 'Questions', component: () => import('@/views/workspace/QuestionsView.vue'), meta: { title: '科学问题题库' } },
        { path: 'experiment-lab', name: 'ExperimentLab', component: () => import('@/views/workspace/ExperimentLab.vue'), meta: { title: '实验模拟场' } },
        // === 课程中心（开课 / 选课 / PPT 电子化阅读 / AI 更新） ===
        { path: 'courses', name: 'Courses', component: () => import('@/views/course/CoursesView.vue'), meta: { title: '课程中心' } },
        { path: 'courseware-studio', name: 'CoursewareStudio', component: () => import('@/views/course/CoursewareStudio.vue'), meta: { title: 'AI 生成 PPT' } },
        { path: 'course/:id', name: 'CourseDetail', component: () => import('@/views/course/CourseDetail.vue'), meta: { title: '课程详情' } },
        { path: 'course/:courseId/read/:cwId', name: 'CoursewareReader', component: () => import('@/views/course/CoursewareReader.vue'), meta: { title: '课件阅读' } },
        { path: 'settings', name: 'Settings', component: () => import('@/views/settings/SettingsView.vue') },
        { path: 'admin', name: 'Admin', component: () => import('@/views/admin/AdminView.vue'), meta: { requiresAdmin: true } },
      ]
    },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next({ name: 'Login' })
  } else if (to.meta.guest && authStore.isLoggedIn) {
    next({ name: 'Dashboard' })
  } else if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
