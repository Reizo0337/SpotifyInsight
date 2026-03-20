<script setup lang="ts">
import { useRouter } from 'vue-router'
import { X, Minus, Square, ChevronLeft } from 'lucide-vue-next'

const router = useRouter()
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
</script>

<template>
  <div v-if="isElectron" class="electron-titlebar">
    <div class="drag-region">
      <div class="app-title">
        <img src="/favicon.svg" alt="logo" class="logo" />
        <span>SpotifyInsight</span>
      </div>
    </div>
    
    <div class="controls">
      <button @click="goBack" class="control-btn back-btn" title="Atrás">
        <ChevronLeft :size="18" />
      </button>
      <div class="divider"></div>
      <button @click="minimize" class="control-btn" title="Minimizar">
        <Minus :size="16" />
      </button>
      <button @click="toggleMaximize" class="control-btn" title="Maximizar">
        <Square :size="14" />
      </button>
      <button @click="close" class="control-btn close-btn" title="Cerrar">
        <X :size="18" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.electron-titlebar {
  height: 32px;
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
}

.drag-region {
  flex: 1;
  height: 100%;
  display: flex;
  align-items: center;
  padding-left: 12px;
  -webkit-app-region: drag;
}

.app-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 600;
  color: #b3b3b3;
}

.logo {
  width: 14px;
  height: 14px;
}

.controls {
  display: flex;
  height: 100%;
  -webkit-app-region: no-drag;
}

.control-btn {
  width: 46px;
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

.control-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.close-btn:hover {
  background: #e81123 !important;
  color: white !important;
}

.back-btn {
  width: 32px;
  color: #efefef;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.15);
}

.divider {
  width: 1px;
  height: 16px;
  background: rgba(255, 255, 255, 0.1);
  align-self: center;
  margin: 0 4px;
}
</style>
