<script setup lang="ts">
import { onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Player from './components/Player.vue'
import TitleBar from './components/TitleBar.vue'
import { RouterView, RouterLink } from 'vue-router'
import { useMusicStore } from './stores/musicStore'
import { Home, Search, Layers } from 'lucide-vue-next'
import CreatePlaylistModal from './components/CreatePlaylistModal.vue'

import { useRouter } from 'vue-router'

const musicStore = useMusicStore()
const router = useRouter()
const isElectron = !!(window as any).electronAPI

onMounted(async () => {
  musicStore.loadPlaybackState()
  // Fetch all data in parallel — critical for playlists to persist on refresh
  await Promise.all([
    musicStore.fetchAllData(),
    musicStore.fetchPlaylists(),
    musicStore.fetchFavorites(),
  ])
  if (isElectron) {
    document.body.classList.add('is-electron')
  }
  
  // Ensure we start at Explorar
  router.push('/')
})
</script>

<template>
  <TitleBar v-if="isElectron" />
  <Sidebar />
  <main class="main-content">
    <div class="view-container">
      <RouterView />
    </div>
  </main>

  <nav class="mobile-nav">
    <RouterLink to="/" class="m-nav-item">
      <Home :size="24" />
      <span>Inicio</span>
    </RouterLink>
    <RouterLink to="/search" class="m-nav-item">
      <Search :size="24" />
      <span>Buscar</span>
    </RouterLink>
    <RouterLink to="/wrapped" class="m-nav-item">
      <Layers :size="24" />
      <span>Wrapped</span>
    </RouterLink>
  </nav>

  <Player />
  <CreatePlaylistModal />
</template>

<style>
/* Global-ish styles to fix Electron layout */
body.is-electron #app {
  padding-top: 64px !important; /* New TitleBar height + extra breath */
}
</style>

<style scoped>
.mobile-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0; right: 0;
  height: 64px;
  background: rgba(10, 10, 10, 0.8);
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  z-index: 1001;
  padding: 0 16px;
  justify-content: space-around;
  align-items: center;
}

@media (max-width: 768px) {
  .mobile-nav {
    display: flex;
  }
}

.m-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: var(--spotify-text-grey);
  text-decoration: none;
  font-size: 0.65rem;
  font-weight: 700;
}

.m-nav-item.router-link-active {
  color: white;
}



.view-container {
    padding: 0 16px;
}

@media (max-width: 768px) {
  .view-container {
    padding: 0 8px;
    padding-bottom: 160px;
  }
}
</style>
