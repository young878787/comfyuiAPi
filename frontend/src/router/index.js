import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import DrawView from '@/views/DrawView.vue'

const routes = [
  { path: '/', redirect: '/chat' },
  { path: '/chat', name: 'chat', component: ChatView },
  { path: '/draw', name: 'draw', component: DrawView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
