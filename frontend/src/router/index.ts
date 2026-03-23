import { createRouter, createWebHistory } from 'vue-router'
import { useMusicStore } from '../stores/musicStore'
import HomeView from '../views/HomeView.vue'
import AuthView from '../views/AuthView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: AuthView,
      meta: { public: true }
    },
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/wrapped',
      name: 'wrapped',
      component: () => import('../views/WrappedView.vue')
    },
    {
      path: '/stats',
      name: 'stats',
      component: () => import('../views/StatsView.vue')
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('../views/SearchView.vue')
    },
    {
      path: '/collection/tracks',
      name: 'favorites',
      component: () => import('../views/FavoritesView.vue')
    },
    {
      path: '/playlist/:id',
      name: 'playlist',
      component: () => import('../views/PlaylistView.vue')
    }
  ]
})

// Global Navigation Guard
router.beforeEach((to, _from) => {
  const musicStore = useMusicStore()
  if (!to.meta.public && !musicStore.accessToken) {
    return '/login'
  } else if (to.name === 'login' && musicStore.accessToken) {
    return '/'
  }
})

export default router
