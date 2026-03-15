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

const formatTime = (ms: number) => {
  if (!ms || isNaN(ms)) return '0:00'
  const secs = Math.floor(ms / 1000)
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
      <div class="play-icon-row">
        <Play :size="16" fill="white" />
      </div>
    </div>
    
    <div class="info-col">
      <div class="thumb">
          <img :src="track.thumbnail && track.thumbnail !== 'Unknown' ? track.thumbnail : `https://api.dicebear.com/7.x/shapes/svg?seed=${track.track_name}`" alt="">
      </div>
      <div class="details">
        <span class="name">{{ track.track_name }}</span>
        <span class="artist">{{ track.artist }}</span>
      </div>
    </div>

    <div class="album-col">{{ track.album }}</div>
    
    <div class="actions-col">
      <button class="action-btn" title="Me gusta"><Heart :size="18" /></button>
      <span class="duration">{{ formatTime(track.duration_ms || track.duration) }}</span>
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
  padding: 8px 16px;
  border-radius: 8px;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--spotify-text-grey);
}

.track-row-2026:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--spotify-text-white);
}

.index-col {
  display: flex;
  justify-content: center;
  position: relative;
  width: 32px;
}

.play-icon-row { display: none; color: white; }
.track-row-2026:hover .number { display: none; }
.track-row-2026:hover .play-icon-row { display: block; }

.info-col { display: flex; align-items: center; gap: 12px; }
.thumb { width: 40px; height: 40px; border-radius: 4px; overflow: hidden; background: #282828; flex-shrink: 0; }
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.details { display: flex; flex-direction: column; overflow: hidden; }
.name { color: white; font-weight: 500; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.artist { font-size: 0.8rem; }
.album-col { font-size: 0.8rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.actions-col { display: flex; align-items: center; gap: 12px; justify-content: flex-end; }
.action-btn { opacity: 0; transition: opacity 0.2s; color: var(--spotify-text-grey); }
.track-row-2026:hover .action-btn { opacity: 1; }
.action-btn:hover { color: white; }
.duration { font-size: 0.8rem; min-width: 40px; text-align: right; font-variant-numeric: tabular-nums; }
.menu-container { position: relative; }
.track-menu { position: absolute; top: 100%; right: 0; background: #282828; border-radius: 4px; box-shadow: 0 16px 24px rgba(0,0,0,0.4); padding: 4px; min-width: 220px; z-index: 100; }
.track-menu button { width: 100%; padding: 12px; font-size: 0.85rem; color: #b3b3b3; text-align: left; border-radius: 2px; display: flex; align-items: center; gap: 12px; }
.track-menu button:hover { background: rgba(255,255,255,0.1); color: white; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.95); }
</style>
