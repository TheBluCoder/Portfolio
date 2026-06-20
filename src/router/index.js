import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import ProjectView from '@/views/ProjectView.vue'
import GalleryView from '@/views/GalleryView.vue'
import PoemDetailView from '@/views/PoemDetailView.vue'
import AdminView from '@/views/AdminView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/projects', name: 'projects', component: ProjectView },
    { path: '/gallery', name: 'gallery', component: GalleryView },
    { path: '/poem/:poemId', name: 'poem-detail', component: PoemDetailView },
    { path: '/admin', name: 'admin', component: AdminView },
  ],
})

export default router
