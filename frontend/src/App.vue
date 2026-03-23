<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import Player from './components/Player.vue'
import TitleBar from './components/TitleBar.vue'
import { RouterView, RouterLink } from 'vue-router'
import { useMusicStore } from './stores/musicStore'
import { Home, Search, Layers } from 'lucide-vue-next'
import CreatePlaylistModal from './components/CreatePlaylistModal.vue'

const musicStore = useMusicStore()
const route = useRoute()
const isElectron = !!(window as any).electronAPI

const isAuthPage = computed(() => route.meta.public === true)

onMounted(async () => {
  if (isAuthPage.value) return 

  musicStore.loadPlaybackState()
  
  if (musicStore.accessToken) {
    // Only fetch data if we have a token
    await musicStore.fetchAllData()
  }
  
  if (isElectron) {
    document.body.classList.add('is-electron')
  }
})
</script>

<template>
  <TitleBar v-if="isElectron" />
  
  <div v-if="!isAuthPage && musicStore.accessToken" class="app-layout">
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
  </div>

  <template v-else>
    <RouterView />
  </template>
</template>

<style>
.app-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width, 280px) 1fr;
  grid-template-rows: 1fr auto;
  grid-template-areas: 
    "sidebar main"
    "player player";
  padding: 12px;
  gap: 12px;
  flex: 1;
  overflow: hidden;
}

.sidebar-nebula {
  grid-area: sidebar;
}

.main-content {
  grid-area: main;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .app-layout {
    grid-template-columns: 1fr;
    grid-template-areas: "main" "player";
    padding: 0;
    gap: 0;
  }
  .sidebar-nebula { display: none; }
}
</style>

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
