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
  <div v-if="isElectron" class="nebula-titlebar">
    <div class="left-section">
      <div class="app-logo">
         <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="var(--nebula-primary)"/>
        </svg>
      </div>
      <div class="nav-controls">
        <button @click="goBack" class="nav-btn" title="Atrás">
          <ChevronLeft :size="18" />
        </button>
        <button @click="goForward" class="nav-btn" title="Adelante">
          <ChevronRight :size="18" />
        </button>
      </div>
    </div>

    <div class="drag-region">
      <span class="app-title">NEBULA MUSIC CORE</span>
    </div>
    
    <div class="right-section">
      <div class="user-pill" v-if="musicStore.userProfile">
        <div class="avatar">
            <img :src="`https://api.dicebear.com/7.x/identicon/svg?seed=${musicStore.userProfile?.username || 'nebula'}`" alt="U">
        </div>
        <span>{{ musicStore.userProfile?.username || 'User' }}</span>
      </div>
      
      <div class="window-controls">
        <button @click="minimize" class="window-btn" title="Minimizar">
          <Minus :size="18" />
        </button>
        <button @click="toggleMaximize" class="window-btn" title="Maximizar">
          <Square :size="14" />
        </button>
        <button @click="close" class="window-btn close-btn" title="Cerrar">
          <X :size="18" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.nebula-titlebar {
  height: 44px;
  background: var(--nebula-bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  user-select: none;
  border-bottom: 1px solid var(--glass-border);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10001;
  padding: 0 12px;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 100%;
}

.app-logo {
  display: flex;
  align-items: center;
}

.nav-controls {
  display: flex;
  gap: 8px;
  -webkit-app-region: no-drag;
}

.nav-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--nebula-surface);
  border: 1px solid var(--glass-border);
  color: var(--nebula-text-dim);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover {
  background: var(--nebula-surface-hover);
  color: white;
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
  font-size: 10px;
  font-weight: 800;
  color: var(--nebula-text-muted);
  letter-spacing: 2px;
  text-transform: uppercase;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 100%;
  -webkit-app-region: no-drag;
}

.user-pill {
    background: var(--nebula-surface);
    border: 1px solid var(--glass-border);
    padding: 2px 12px 2px 4px;
    border-radius: 500px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--nebula-text-dim);
    cursor: pointer;
    transition: all 0.2s;
}

.user-pill:hover {
    background: var(--nebula-surface-hover);
    color: white;
}

.avatar {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    overflow: hidden;
    border: 1px solid var(--nebula-primary);
}

.avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.window-controls {
  display: flex;
  height: 100%;
  margin-left: 8px;
}

.window-btn {
  width: 44px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--nebula-text-dim);
  cursor: pointer;
  transition: all 0.2s;
}

.window-btn:hover {
  background: var(--nebula-surface-hover);
  color: white;
}

.close-btn:hover {
  background: #ff4444 !important;
  color: white !important;
}
</style>
