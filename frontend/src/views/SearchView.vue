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
      <h2>Explorar todo</h2>
      <div class="category-grid">
        <div class="cat-card podcast">Podcasts</div>
        <div class="cat-card events">Eventos</div>
        <div class="cat-card made-for-you">Especialmente para ti</div>
        <div class="cat-card new-releases">Nuevos lanzamientos</div>
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
