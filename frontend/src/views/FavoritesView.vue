<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { Heart, Play } from 'lucide-vue-next'
import { useMusicStore } from '../stores/musicStore'
import TrackRow from '../components/TrackRow.vue'

const musicStore = useMusicStore()

const playAll = () => {
  if (musicStore.favorites.length > 0) {
    musicStore.setNowPlaying(musicStore.favorites[0], musicStore.favorites)
  }
}

onMounted(() => {
  musicStore.fetchFavorites()
})
</script>

<template>
  <div class="favorites-view">
    <div class="header-banner">
      <div class="icon-box">
        <Heart :size="64" fill="white" />
      </div>
      <div class="info">
        <p class="type">Playlist</p>
        <h1>Canciones que te gustan</h1>
        <p class="meta">
          <span class="user">{{ musicStore.userProfile?.display_name }}</span>
          <span class="dot">•</span>
          <span>{{ musicStore.favorites.length }} canciones</span>
        </p>
      </div>
    </div>

    <div class="controls">
      <button class="play-btn" @click="playAll" :disabled="musicStore.favorites.length === 0">
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
      <TrackRow 
        v-for="(track, index) in musicStore.favorites" 
        :key="track.spotify_id" 
        :track="track" 
        :index="index + 1"
        :contextQueue="musicStore.favorites"
      />
      
      <div v-if="musicStore.favorites.length === 0" class="empty-state">
        <p>Aún no tienes canciones favoritas.</p>
        <RouterLink to="/search" class="find-link">Buscar canciones</RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.favorites-view {
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
  background: linear-gradient(135deg, #450af5, #c4efd9);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
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

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--spotify-text-grey);
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
