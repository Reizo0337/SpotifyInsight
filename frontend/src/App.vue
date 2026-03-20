<script setup lang="ts">
import { onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Player from './components/Player.vue'
import TitleBar from './components/TitleBar.vue'
import { RouterView, RouterLink } from 'vue-router'
import { useMusicStore } from './stores/musicStore'
import { Home, Search, Layers } from 'lucide-vue-next'

const musicStore = useMusicStore()
const isElectron = !!(window as any).electronAPI

onMounted(() => {
  musicStore.loadPlaybackState()
  musicStore.fetchAllData()
  if (isElectron) {
    document.body.classList.add('is-electron')
  }
})
</script>

<template>
  <TitleBar v-if="isElectron" />
  <Sidebar />
  <main class="main-content">
    <div class="top-bar">
      <div></div>
      <div class="user-pill">
        <span>{{ musicStore.userProfile?.user_name || 'Spotify User' }}</span>
        <div class="avatar">{{ musicStore.userProfile?.user_name?.charAt(0) || 'S' }}</div>
      </div>
    </div>
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
</template>

<style>
/* Global-ish styles to fix Electron layout */
body.is-electron #app {
  padding-top: 40px !important; /* Titlebar height + some margin */
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

.top-bar {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    position: sticky;
    top: 0;
    z-index: 50;
    background: transparent;
}

@media (max-width: 768px) {
  .top-bar {
    display: none;
  }
}

.user-pill {
    background: rgba(0,0,0,0.7);
    padding: 2px 2px 2px 12px;
    border-radius: 32px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    font-weight: 700;
}

.avatar {
    width: 28px;
    height: 28px;
    background: #535353;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
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
