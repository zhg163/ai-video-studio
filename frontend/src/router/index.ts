import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/views/HomeView.vue'),
    },
    {
      path: '/projects',
      component: () => import('@/views/ProjectsView.vue'),
    },
    {
      path: '/projects/:id',
      component: () => import('@/views/ProjectDetailView.vue'),
      children: [
        {
          path: '',
          redirect: (to) => `/projects/${to.params.id}/brief`,
        },
        {
          path: 'brief',
          component: () => import('@/views/BriefView.vue'),
        },
        {
          path: 'script',
          component: () => import('@/views/ScriptView.vue'),
        },
        {
          path: 'storyboard',
          component: () => import('@/views/StoryboardView.vue'),
        },
        {
          path: 'timeline',
          component: () => import('@/views/TimelineView.vue'),
        },
        {
          path: 'render',
          component: () => import('@/views/RenderView.vue'),
        },
      ],
    },
  ],
})

export default router
