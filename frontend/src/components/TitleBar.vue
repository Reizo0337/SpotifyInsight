<script setup lang="ts">
import { useRouter } from 'vue-router'
import { X, Minus, Square, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { useMusicStore } from '../stores/musicStore'

const router = useRouter()
const musicStore = useMusicStore()
const isElectron = !!(window as any).electronAPI

const close = () => {
  if (isElectron) (window as any).electronAPI.window.close()
}

const minimize = () => {
  if (isElectron) (window as any).electronAPI.window.minimize()
}

const toggleMaximize = () => {
  if (isElectron) (window as any).electronAPI.window.toggleMaximize()
}

const goBack = () => {
  router.back()
}

const goForward = () => {
  router.forward()
}
</script>

<template>
  <div v-if="isElectron" class="electron-titlebar">
    <div class="left-section">
      <div class="app-logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="#1565FF" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.49 17.29c-.22.35-.67.46-1.02.24-2.84-1.74-6.42-2.13-10.63-1.18-.4.09-.79-.16-.88-.55-.09-.4.16-.79.55-.88 4.62-1.05 8.58-.6 11.75 1.34.34.22.45.67.23 1.03zm1.46-3.26c-.27.44-.85.59-1.3.31-3.25-1.99-8.2-2.58-12.04-1.41-.5.15-1.02-.13-1.17-.63-.15-.5.13-1.02.63-1.17 4.41-1.34 9.87-.67 13.57 1.6.45.27.6.85.31 1.3zm.14-3.41c-3.9-2.31-10.32-2.53-14.07-1.39-.6.18-1.24-.16-1.42-.76-.18-.6.16-1.24.76-1.42 4.31-1.31 11.41-1.05 15.93 1.63.54.32.72 1.02.4 1.56-.32.54-1.02.72-1.6.4z"/>
        </svg>
      </div>
      <div class="nav-controls">
        <button @click="goBack" class="nav-btn" title="Atrás">
          <ChevronLeft :size="24" />
        </button>
        <button @click="goForward" class="nav-btn" title="Adelante">
          <ChevronRight :size="24" />
        </button>
      </div>
    </div>

    <div class="drag-region">
      <span class="app-title">Spotipy Insight</span>
    </div>
    
    <div class="right-section">
      <div class="user-pill">
        <span>{{ musicStore.userProfile?.user_name || 'Spotify User' }}</span>
        <div class="avatar">{{ musicStore.userProfile?.user_name?.charAt(0) || 'S' }}</div>
      </div>
      <div class="window-controls">
        <button @click="minimize" class="window-btn" title="Minimizar">
          <Minus :size="20" />
        </button>
        <button @click="toggleMaximize" class="window-btn" title="Maximizar">
          <Square :size="16" />
        </button>
        <button @click="close" class="window-btn close-btn" title="Cerrar">
          <X :size="20" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.electron-titlebar {
  height: 48px;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  user-select: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  padding: 0 8px;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 100%;
}

.app-logo {
  padding-left: 8px;
  display: flex;
  align-items: center;
}

.nav-controls {
  display: flex;
  gap: 8px;
  -webkit-app-region: no-drag;
}

.nav-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(0,0,0,0.7);
  border: none;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover {
  background: rgba(255,255,255,0.1);
}

.drag-region {
  flex: 1;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  -webkit-app-region: drag;
}

.app-title {
  font-size: 11px;
  font-weight: 700;
  color: #b3b3b3;
  letter-spacing: 1px;
  text-transform: uppercase;
  opacity: 0.8;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 100%;
  -webkit-app-region: no-drag;
}

.user-pill {
    background: rgba(40, 40, 40, 0.7);
    padding: 2px 2px 2px 12px;
    border-radius: 32px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    font-weight: 700;
    color: white;
    cursor: pointer;
}

.user-pill:hover {
    background: rgba(60, 60, 60, 0.8);
}

.avatar {
    width: 28px;
    height: 28px;
    background: #535353;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
}

.window-controls {
  display: flex;
  height: 100%;
}

.window-btn {
  width: 48px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #b3b3b3;
  cursor: pointer;
  transition: all 0.2s;
}

.window-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.close-btn:hover {
  background: #e81123 !important;
  color: white !important;
}
</style>
