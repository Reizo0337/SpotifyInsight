<script setup lang="ts">
import { useMusicStore } from '../stores/musicStore'
import { useRouter } from 'vue-router'
import { ChevronLeft, TrendingUp, Users, Radio, Disc } from 'lucide-vue-next'

const musicStore = useMusicStore()
const router = useRouter()

const formatPercent = (val: number) => Math.round(val * 100) + '%'
</script>

<template>
  <div class="stats-view">
    <button @click="router.back()" class="back-btn">
      <ChevronLeft :size="20" />
      <span>Volver</span>
    </button>

    <header class="header">
      <h1>Estadísticas Detalladas</h1>
      <p>Un análisis profundo de tus hábitos y preferencias musicales en SpotifyInsights.</p>
    </header>

    <div class="stats-grid">
      <section class="stat-section main-stats">
        <h2>Atributos de Audio</h2>
        <div class="audio-features">
          <div class="feature-row" v-for="(val, key) in { 
            'Energía': musicStore.stats?.avg_energy, 
            'Bailabilidad': musicStore.stats?.avg_danceability,
            'Valencia (Positividad)': musicStore.stats?.avg_valence,
            'Acústica': musicStore.userProfile?.features?.acousticness || 0,
            'Instrumentalidad': musicStore.userProfile?.features?.instrumentalness || 0
          }" :key="key">
            <span class="f-label">{{ key }}</span>
            <div class="f-bar-bg">
              <div class="f-bar-fill" :style="{ width: formatPercent(val || 0) }"></div>
            </div>
            <span class="f-val">{{ formatPercent(val || 0) }}</span>
          </div>
        </div>
      </section>

      <section class="stat-section">
        <h2><Users :size="20" /> Top Artistas</h2>
        <div class="list">
          <div v-for="(count, artist) in musicStore.stats?.top_artists" :key="artist" class="list-item">
            <span class="item-name">{{ artist }}</span>
            <span class="item-meta">{{ count }} canciones</span>
          </div>
        </div>
      </section>

      <section class="stat-section">
        <h2><Radio :size="20" /> Géneros Dominantes</h2>
        <div class="list">
          <div v-for="(count, genre) in musicStore.stats?.top_genres" :key="genre" class="list-item">
            <span class="item-name">{{ genre }}</span>
            <span class="item-meta">{{ count }}% afinidad</span>
          </div>
        </div>
      </section>

      <section class="stat-section highlights">
        <h2>Hitos de tu Biblioteca</h2>
        <div class="highlight-cards">
          <div class="h-card">
            <TrendingUp :size="24" color="#1565FF" />
            <span class="h-label">Popularidad Media</span>
            <span class="h-val">{{ Math.round(musicStore.stats?.avg_popularity || 0) }}/100</span>
          </div>
          <div class="h-card">
            <Disc :size="24" color="#00d4ff" />
            <span class="h-label">Total Canciones</span>
            <span class="h-val">{{ musicStore.stats?.total_tracks }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.stats-view {
  padding: 40px;
  display: flex;
  flex-direction: column;
  gap: 40px;
  animation: fadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--spotify-text-grey);
  font-weight: 700;
  width: fit-content;
  transition: all 0.3s;
}

.back-btn:hover { color: white; transform: translateX(-4px); }

h1 { font-size: 3.5rem; letter-spacing: -2px; }

.header p { color: var(--spotify-text-grey); font-size: 1.25rem; max-width: 600px; line-height: 1.6; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 32px;
}

.stat-section {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  padding: 32px;
  border-radius: 24px;
  border: 1px solid var(--glass-border);
}

h2 {
  font-size: 1.5rem;
  margin-bottom: 32px;
  display: flex;
  align-items: center;
  gap: 16px;
  font-weight: 800;
}

.audio-features {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.feature-row {
  display: grid;
  grid-template-columns: 140px 1fr 60px;
  align-items: center;
  gap: 20px;
}

.f-label { font-size: 0.9rem; color: var(--spotify-text-grey); font-weight: 600; }

.f-bar-bg {
  height: 10px;
  background: rgba(255,255,255,0.05);
  border-radius: 5px;
  overflow: hidden;
}

.f-bar-fill {
  height: 100%;
  background: var(--spotify-green);
  border-radius: 5px;
  transition: width 1.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 0 15px rgba(21, 101, 255, 0.3);
}

.f-val { font-size: 1rem; font-weight: 800; text-align: right; }

.list { display: flex; flex-direction: column; gap: 12px; }

.list-item {
  display: flex;
  justify-content: space-between;
  padding: 16px 20px;
  background: rgba(255,255,255,0.02);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.03);
}

.item-name { font-weight: 700; }
.item-meta { color: var(--spotify-green); font-weight: 700; font-size: 0.85rem; }

.highlight-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.h-card {
  background: rgba(255,255,255,0.03);
  padding: 32px 20px;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  border: 1px solid rgba(255,255,255,0.05);
}

.h-label { font-size: 0.75rem; color: var(--spotify-text-grey); font-weight: 800; letter-spacing: 1px; }
.h-val { font-size: 2rem; font-weight: 900; }

@media (max-width: 768px) {
    .stats-view { padding: 24px; }
    h1 { font-size: 2.5rem; }
    .stats-grid { grid-template-columns: 1fr; }
    .feature-row { grid-template-columns: 1fr; gap: 8px; }
    .f-val { text-align: left; }
    .highlight-cards { grid-template-columns: 1fr; }
}
</style>
