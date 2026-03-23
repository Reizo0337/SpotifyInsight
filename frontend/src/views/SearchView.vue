<script setup lang="ts">
import { ref, watch } from 'vue'
import { useMusicStore } from '../stores/musicStore'
import { Search as SearchIcon, Loader2 } from 'lucide-vue-next'
import TrackRow from '../components/TrackRow.vue'

const query = ref('')
const musicStore = useMusicStore()

let timeout: any = null

watch(query, (newVal) => {
  if (timeout) clearTimeout(timeout)
  timeout = setTimeout(() => {
    if (newVal) musicStore.search(newVal)
  }, 500)
})
</script>

<template>
  <div class="search-view">
    <div class="search-bar-container">
      <div class="search-input-wrapper">
        <SearchIcon :size="20" class="s-icon" />
        <input 
          v-model="query" 
          type="text" 
          placeholder="¿Qué quieres escuchar?" 
          autofocus
        />
        <Loader2 v-if="musicStore.isLoading" :size="20" class="loading-spinner" />
      </div>
    </div>

    <div class="search-results" v-if="query">
      <h2 v-if="musicStore.searchResults.length > 0">Resultados para "{{ query }}"</h2>
      <div class="results-list">
        <TrackRow 
          v-for="track in musicStore.searchResults" 
          :key="track.id" 
          :track="track"
          :contextQueue="musicStore.searchResults"
        />
      </div>
      <div v-if="!musicStore.isLoading && musicStore.searchResults.length === 0" class="no-results">
        No se encontraron resultados para "{{ query }}"
      </div>
    </div>

    <div class="categories" v-else>
      <div class="category-section">
        <h2>Explorar todo</h2>
        <div class="category-grid">
          <div class="cat-card podcast">Podcasts</div>
          <div class="cat-card events">Eventos</div>
          <div class="cat-card made-for-you">Especialmente para ti</div>
          <div class="cat-card new-releases">Nuevos lanzamientos</div>
        </div>
      </div>

      <div class="recent-played-section" v-if="musicStore.recentTracks.length > 0">
        <div class="section-header">
          <h2>Canciones escuchadas recientemente</h2>
          <span class="view-all">Ver todo</span>
        </div>
        <div class="history-list">
          <TrackRow 
            v-for="(track, index) in musicStore.recentTracks.slice(0, 25)" 
            :key="track.spotify_id + '_' + index" 
            :track="track"
            :index="index + 1"
            :showPlayedAt="true"
            :contextQueue="musicStore.recentTracks.slice(0, 25)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-view {
  padding: 20px;
}

.search-bar-container {
  position: sticky;
  top: 0;
  padding: 10px 0 24px 0;
  background: transparent;
  z-index: 10;
}

.search-input-wrapper {
  position: relative;
  max-width: 400px;
}

.s-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--spotify-dark);
}

input {
  width: 100%;
  padding: 12px 12px 12px 48px;
  border-radius: 500px;
  border: none;
  font-size: 0.9rem;
  font-weight: 500;
  background: white;
  color: black;
}

input:focus {
  outline: none;
}

.loading-spinner {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: black;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 24px;
}

.cat-card {
  aspect-ratio: 1;
  border-radius: 8px;
  padding: 16px;
  font-weight: 700;
  font-size: 1.4rem;
  cursor: pointer;
  transition: transform 0.2s;
}

.cat-card:hover { transform: scale(1.02); }

.podcast { background: #e13300; }
.events { background: #7358ff; }
.made-for-you { background: #1e3264; }
.new-releases { background: #e8115b; }

.no-results {
  padding: 40px;
  text-align: center;
  color: var(--spotify-text-grey);
}

.category-section {
  margin-bottom: 40px;
}

.recent-played-section {
  margin-top: 20px;
  padding-bottom: 100px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.view-all {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--spotify-text-grey);
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.view-all:hover {
  text-decoration: underline;
  color: white;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

h2 {
  font-size: 1.5rem;
  font-weight: 800;
  margin-bottom: 20px;
  letter-spacing: -0.02em;
}

@media (max-width: 768px) {
  .search-view { padding: 12px; }
  .category-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .cat-card {
    font-size: 1.1rem;
    padding: 12px;
  }
}
</style>
