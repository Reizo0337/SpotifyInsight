<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Heart, MoreHorizontal, ListPlus, Play, ChevronRight, Hash } from 'lucide-vue-next'
import { useMusicStore } from '../stores/musicStore'

const props = defineProps<{
  track: any
  index?: number
  contextQueue?: any[]
  showPlayedAt?: boolean
}>()

const store = useMusicStore()
const showMenu = ref(false)
const showPlaylistSubmenu = ref(false)
const menuRef = ref<HTMLElement | null>(null)

const isFavorite = computed(() => {
  return store.favorites.some((t: any) => t.spotify_id === props.track.spotify_id)
})

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

const toggleFavorite = (e: Event) => {
  e.stopPropagation()
  store.toggleFavorite(props.track)
}

const addToPlaylist = async (playlistId: string) => {
  await store.addTrackToPlaylist(playlistId, props.track)
  showMenu.value = false
  showPlaylistSubmenu.value = false
}

const formatTime = (ms: number) => {
  if (!ms || isNaN(ms)) return '0:00'
  const secs = Math.floor(ms / 1000)
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

const formatPlayedAt = (timestamp: number) => {
  if (!timestamp) return ''
  const now = Date.now() / 1000
  const diff = now - timestamp
  if (diff < 60) return 'Ahora'
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  return new Date(timestamp * 1000).toLocaleDateString()
}

const toggleMenu = (e: Event) => {
  e.stopPropagation()
  showMenu.value = !showMenu.value
  showPlaylistSubmenu.value = false
}

const closeMenu = (e: MouseEvent) => {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    showMenu.value = false
    showPlaylistSubmenu.value = false
  }
}

onMounted(() => window.addEventListener('click', closeMenu))
onUnmounted(() => window.removeEventListener('click', closeMenu))

</script>

<template>
  <div class="track-item-nebula" @click="handlePlay">
    <div class="column-index">
      <span class="idx-text">{{ index }}</span>
      <div class="play-peek"><Play :size="14" fill="currentColor" /></div>
    </div>
    
    <div class="column-main">
      <div class="track-thumb">
          <img :src="track.thumbnail && track.thumbnail !== 'Unknown' ? track.thumbnail : `https://api.dicebear.com/7.x/shapes/svg?seed=${track.track_name}`" alt="">
          <div class="thumb-overlay"><Play :size="16" fill="white" /></div>
      </div>
      <div class="track-meta">
        <span class="track-name">{{ track.track_name }}</span>
        <span class="track-artist">{{ track.artist }}</span>
      </div>
    </div>

    <div class="column-album">{{ track.album }}</div>
    
    <div class="column-actions">
      <div v-if="showPlayedAt && track.played_at" class="played-badge">
          <Hash :size="10" />
          {{ formatPlayedAt(track.played_at) }}
      </div>
      
      <button class="fav-btn" :class="{ 'is-fav': isFavorite }" @click="toggleFavorite">
        <Heart :size="18" :fill="isFavorite ? 'var(--nebula-primary)' : 'none'" />
      </button>

      <span class="track-time">{{ formatTime(track.duration_ms || track.duration) }}</span>

      <div class="menu-anchor" ref="menuRef">
        <button class="opt-btn" @click="toggleMenu">
          <MoreHorizontal :size="18" />
        </button>
        <Transition name="menu">
          <div v-if="showMenu" class="item-menu glass">
            <button @click="playNext"><Play :size="14" /> Procesar Siguiente</button>
            <button @click="addToQueue"><ListPlus :size="14" /> Encolar Registro</button>
            <div class="divider"></div>
            <button @click="toggleFavorite">
               <Heart :size="14" :fill="isFavorite ? 'var(--nebula-primary)' : 'none'" /> 
               {{ isFavorite ? 'Remover de Favoritos' : 'Sincronizar Favorito' }}
            </button>
            <div class="sub-trigger" @mouseenter="showPlaylistSubmenu = true">
                <button class="has-sub">
                    <ListPlus :size="14" /> Asignar a Colección
                    <ChevronRight :size="14" class="arr" />
                </button>
                <Transition name="menu">
                    <div v-if="showPlaylistSubmenu" class="sub-board glass" @mouseleave="showPlaylistSubmenu = false">
                        <button v-for="pl in store.playlists" :key="pl.id" @click="addToPlaylist(pl.id)">
                            {{ pl.name }}
                        </button>
                    </div>
                </Transition>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
.track-item-nebula {
  display: grid;
  grid-template-columns: 40px 5fr 3fr minmax(180px, auto);
  padding: 12px 16px;
  border-radius: 16px;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--nebula-text-dim);
  border: 1px solid transparent;
}

.track-item-nebula:hover {
  background: var(--nebula-surface-hover);
  border-color: var(--glass-border);
  transform: scale(1.005) translateX(4px);
  color: white;
}

.column-index {
  display: flex;
  justify-content: center;
  position: relative;
  font-family: 'Space Mono', monospace;
  font-size: 0.8rem;
  opacity: 0.5;
}

.play-peek { display: none; color: var(--nebula-primary); }
.track-item-nebula:hover .idx-text { display: none; }
.track-item-nebula:hover .play-peek { display: flex; }

.column-main { display: flex; align-items: center; gap: 16px; overflow: hidden; }

.track-thumb {
    width: 48px; height: 48px;
    border-radius: 10px;
    position: relative;
    overflow: hidden;
    background: #000;
    flex-shrink: 0;
    border: 1px solid var(--glass-border);
}
.track-thumb img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.4s; }
.track-item-nebula:hover .track-thumb img { transform: scale(1.1); }

.thumb-overlay {
    position: absolute; inset: 0;
    background: rgba(0,0,0,0.4);
    display: flex; align-items: center; justify-content: center;
    opacity: 0; transition: opacity 0.2s;
}
.track-item-nebula:hover .thumb-overlay { opacity: 1; }

.track-meta { display: flex; flex-direction: column; gap: 2px; overflow: hidden; }
.track-name { font-size: 0.95rem; font-weight: 700; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.track-artist { font-size: 0.75rem; color: var(--nebula-text-dim); }

.column-album { font-size: 0.8rem; color: var(--nebula-text-muted); padding-right: 20px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.column-actions { display: flex; align-items: center; gap: 18px; justify-content: flex-end; }

.played-badge {
    display: flex; align-items: center; gap: 4px;
    background: rgba(99, 102, 241, 0.1);
    color: var(--nebula-primary);
    padding: 4px 10px; border-radius: 500px;
    font-size: 0.65rem; font-weight: 800;
}

.fav-btn {
    color: var(--nebula-text-muted);
    transition: all 0.2s;
    opacity: 0.4;
}
.track-item-nebula:hover .fav-btn { opacity: 1; }
.fav-btn.is-fav { color: var(--nebula-primary); opacity: 1; filter: drop-shadow(0 0 5px var(--nebula-primary)); }
.fav-btn:hover { transform: scale(1.2); color: white; }

.track-time { font-size: 0.8rem; font-weight: 600; opacity: 0.6; min-width: 45px; text-align: right; font-variant-numeric: tabular-nums; }

.menu-anchor { position: relative; }
.opt-btn { color: var(--nebula-text-muted); opacity: 0; transition: opacity 0.2s; }
.track-item-nebula:hover .opt-btn { opacity: 1; }
.opt-btn:hover { color: white; }

.item-menu {
    position: absolute; top: calc(100% + 10px); right: 0;
    padding: 8px; border-radius: 16px;
    min-width: 260px; z-index: 1000;
    box-shadow: 0 20px 50px rgba(0,0,0,0.6);
}
.item-menu button {
    width: 100%; padding: 12px 14px;
    font-size: 0.85rem; font-weight: 600;
    color: var(--nebula-text-dim);
    display: flex; align-items: center; gap: 12px;
    border-radius: 10px; transition: all 0.2s;
}
.item-menu button:hover { background: var(--nebula-surface-hover); color: white; }

.divider { height: 1px; background: var(--glass-border); margin: 6px 0; }

.sub-trigger { position: relative; }
.has-sub { justify-content: space-between !important; }
.sub-board {
    position: absolute; left: calc(-100% - 12px); top: 0;
    padding: 8px; border-radius: 16px;
    min-width: 200px; z-index: 1001;
}

.menu-enter-active, .menu-leave-active { transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
.menu-enter-from, .menu-leave-to { opacity: 0; transform: translateY(8px) scale(0.95); }

@media (max-width: 900px) {
    .column-album { display: none; }
    .track-item-nebula { grid-template-columns: 40px 1fr auto; }
}

@media (max-width: 600px) {
    .track-item-nebula { padding: 8px; border-radius: 12px; }
    .column-index, .track-time, .played-badge { display: none; }
}
</style>
