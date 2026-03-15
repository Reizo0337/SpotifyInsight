<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Heart, MoreHorizontal, ListPlus, Play } from 'lucide-vue-next'
import { useMusicStore } from '../stores/musicStore'

const props = defineProps<{
  track: any
  index?: number
  contextQueue?: any[]
}>()

const store = useMusicStore()
const showMenu = ref(false)
const menuRef = ref<HTMLElement | null>(null)

const handlePlay = () => {
    store.setNowPlaying(props.track, props.contextQueue)
}

const addToQueue = () => {
  store.addToQueue(props.track)
  showMenu.value = false
}

const playNext = () => {
  store.insertNext(props.track)
  showMenu.value = false
}

const formatTime = (secs: number) => {
  if (!secs || isNaN(secs)) return '0:00'
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

const toggleMenu = (e: Event) => {
  e.stopPropagation()
  showMenu.value = !showMenu.value
}

const closeMenu = (e: MouseEvent) => {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    showMenu.value = false
  }
}

onMounted(() => window.addEventListener('click', closeMenu))
onUnmounted(() => window.removeEventListener('click', closeMenu))

</script>

<template>
  <div class="track-row-2026" @click="handlePlay">
    <div class="index-col">
      <span class="number" v-if="index !== undefined">{{ index }}</span>
      <div class="play-icon-wrapper">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
      </div>
    </div>
    
    <div class="info-col">
      <div class="thumb">
          <img :src="track.thumbnail || `https://api.dicebear.com/7.x/shapes/svg?seed=${track.track_name}`" alt="Art">
      </div>
      <div class="details">
        <span class="name">{{ track.track_name }}</span>
        <span class="artist">{{ track.artist }}</span>
      </div>
    </div>

    <div class="album-col">{{ track.album }}</div>
    
    <div class="actions-col">
      <button class="action-btn" title="Me gusta"><Heart :size="18" /></button>
      <span class="duration">{{ formatTime(track.duration) }}</span>
      <div class="menu-container" ref="menuRef">
        <button class="action-btn opt" @click="toggleMenu" title="Más opciones">
          <MoreHorizontal :size="18" />
        </button>
        <Transition name="fade">
          <div v-if="showMenu" class="track-menu">
            <button @click="playNext"><Play :size="14" /> Reproducir a continuación</button>
            <button @click="addToQueue"><ListPlus :size="14" /> Añadir a la cola</button>
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
.track-row-2026 {
  display: grid;
  grid-template-columns: 48px 4fr 3fr 140px;
  padding: 12px 16px;
  border-radius: 12px;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--spotify-text-grey);
  border: 1px solid transparent;
}

.track-row-2026:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--spotify-text-white);
  border-color: rgba(255, 255, 255, 0.05);
  transform: translateX(4px);
}

.track-row-2026:hover .number { display: none; }
.track-row-2026:hover .play-icon { display: block; }

.index-col {
  display: flex;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
}

.play-icon { display: none; color: white; }

.info-col {
  display: flex;
  align-items: center;
  gap: 16px;
}

.thumb {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--spotify-light-grey);
}

.thumb img {
    width: 100%; height: 100%;
}

.details {
  display: flex;
  flex-direction: column;
}

.name {
  color: var(--spotify-text-white);
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: -0.01em;
}

.artist {
  font-size: 0.85rem;
  font-weight: 500;
}

.album-col {
  font-size: 0.85rem;
  font-weight: 500;
}

.actions-col {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: flex-end;
}

.action-btn {
  opacity: 0;
  transition: opacity 0.2s;
  color: var(--spotify-text-grey);
}

.track-row-2026:hover .action-btn {
  opacity: 1;
}

.action-btn:hover {
    color: white;
}

.opt { margin-left: 4px; }

.duration {
  font-size: 0.85rem;
  font-weight: 600;
  width: 45px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* ─── Track Menu ────────────────────────────────── */
.menu-container {
  position: relative;
}

.track-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: #282828;
  border-radius: 4px;
  box-shadow: 0 16px 24px rgba(0,0,0,0.3), 0 6px 8px rgba(0,0,0,0.2);
  padding: 4px;
  min-width: 220px;
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.track-menu button {
  padding: 12px 14px;
  font-size: 0.85rem;
  font-weight: 500;
  color: #b3b3b3;
  text-align: left;
  border-radius: 2px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.track-menu button:hover {
  background: rgba(255,255,255,0.1);
  color: white;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
