<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Library, Play } from 'lucide-vue-next'
import { useMusicStore } from '../stores/musicStore'
import TrackRow from '../components/TrackRow.vue'

const route = useRoute()
const musicStore = useMusicStore()

const playlistId = computed(() => route.params.id as string)
const playlist = computed(() => musicStore.playlists.find((p: any) => p.id === playlistId.value))

const playlistTracks = ref<any[]>([])
const isLoading = ref(false)

const fetchTracks = async () => {
  if (!playlist.value || !playlist.value.tracks || playlist.value.tracks.length === 0) {
    playlistTracks.value = []
    return
  }
  
  isLoading.value = true
  try {
    const ids = playlist.value.tracks.join(',')
    const data = await musicStore._apiCall('/music/tracks', { ids })
    if (data) {
      playlistTracks.value = data
    }
  } catch (e) {
    console.error('Fetch playlist tracks failed', e)
  } finally {
    isLoading.value = false
  }
}

const playAll = () => {
  if (playlistTracks.value.length > 0) {
    musicStore.setNowPlaying(playlistTracks.value[0], playlistTracks.value)
  }
}

onMounted(() => {
  fetchTracks()
})

watch(playlistId, () => {
  fetchTracks()
})
</script>

<template>
  <div class="playlist-view" v-if="playlist">
    <div class="header-banner">
      <div class="icon-box">
        <Library :size="64" />
      </div>
      <div class="info">
        <p class="type">{{ playlist.is_public ? 'Playlist Pública' : 'Playlist Privada' }}</p>
        <h1>{{ playlist.name }}</h1>
        <p class="meta">
          <span class="user">{{ musicStore.userProfile?.display_name }}</span>
          <span class="dot">•</span>
          <span>{{ playlist.tracks?.length || 0 }} canciones</span>
        </p>
      </div>
    </div>

    <div class="controls">
      <button class="play-btn" @click="playAll" :disabled="playlistTracks.length === 0">
        <Play :size="24" fill="black" />
      </button>
    </div>

    <div class="tracks-list">
      <div class="list-header">
        <div class="index">#</div>
        <div class="title">Título</div>
        <div class="album">Álbum</div>
        <div class="actions"></div>
      </div>
      
      <div v-if="isLoading" class="loading">Cargando canciones...</div>
      
      <TrackRow 
        v-for="(track, index) in playlistTracks" 
        :key="track.spotify_id" 
        :track="track" 
        :index="Number(index) + 1"
        :contextQueue="playlistTracks"
      />
      
      <div v-if="!isLoading && playlistTracks.length === 0" class="empty-state">
        <p>Esta playlist está vacía.</p>
        <RouterLink to="/search" class="find-link">Añadir canciones</RouterLink>
      </div>
    </div>
  </div>
  <div v-else-if="musicStore.playlists.length === 0 && musicStore.accessToken" class="loading-full">
    <div class="spinner-nebula"></div>
    <p>Sincronizando con el servidor...</p>
  </div>
  <div v-else class="not-found">
    Playlist no encontrada
  </div>
</template>

<style scoped>
.playlist-view {
  padding: 24px;
}

.header-banner {
  display: flex;
  align-items: flex-end;
  gap: 24px;
  margin-bottom: 24px;
  background: linear-gradient(transparent, rgba(0,0,0,0.5));
  padding: 40px 0 20px 0;
}

.icon-box {
  width: 192px;
  height: 192px;
  background: #282828;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
  color: #b3b3b3;
}

.info .type {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.info h1 {
  font-size: 4rem;
  font-weight: 900;
  margin: 0 0 16px 0;
  letter-spacing: -2px;
}

.info .meta {
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta .user { color: white; }
.meta .dot { color: rgba(255,255,255,0.7); }

.controls {
  padding: 16px 0;
  margin-bottom: 24px;
}

.play-btn {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--spotify-green);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s, background 0.2s;
}

.play-btn:hover {
  transform: scale(1.05);
  background: #1fdf64;
}

.play-btn:disabled {
    background: #282828;
    cursor: not-allowed;
    transform: none;
}

.tracks-list {
  display: flex;
  flex-direction: column;
}

.list-header {
  display: grid;
  grid-template-columns: 48px 4fr 3fr 120px;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  margin-bottom: 16px;
  color: var(--spotify-text-grey);
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  height: 36px;
  align-items: center;
}

.loading, .empty-state, .not-found, .loading-full {
  text-align: center;
  padding: 60px 0;
  color: var(--spotify-text-grey);
}

.loading-full {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
}

.spinner-nebula {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(99, 102, 241, 0.1);
  border-left-color: var(--nebula-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.find-link {
  display: inline-block;
  margin-top: 16px;
  padding: 12px 32px;
  background: white;
  color: black;
  border-radius: 500px;
  font-weight: 700;
  text-decoration: none;
  transition: transform 0.2s;
}

.find-link:hover {
  transform: scale(1.05);
}
</style>
