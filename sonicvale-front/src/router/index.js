import { createRouter, createWebHashHistory  } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/projects'
  },
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('../pages/ProjectList.vue')
  },
  {
    path: '/config',
    name: 'ConfigCenter',
    component: () => import('../pages/ConfigCenter.vue')
  },
  {
    path: '/voices',
    name: 'VoiceManager',
    component: () => import('../pages/VoiceManager.vue')
  },
  // 配音详情页面（带项目 ID 参数）
  { 
    path: '/projects/:id/dubbing', 
    name: 'ProjectDubbingDetail', 
    component:  () => import('../pages/ProjectDubbingDetail.vue')
  },
  { path: '/prompts',
    name: 'PromptManager', 
    component:() => import('../pages/PromptManager.vue') },    // 新增路由
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
