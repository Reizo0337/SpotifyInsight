<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useMusicStore } from '../stores/musicStore'
import StatCard from '../components/StatCard.vue'
import TrackRow from '../components/TrackRow.vue'
import LoadingScreen from '../components/LoadingScreen.vue'
import { 
  RefreshCcw, Zap, BarChart3, 
  Wind, Activity, 
  ChevronRight, Play, Sparkles
} from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const musicStore = useMusicStore()
const router = useRouter()
const showLoading = ref(true)

onMounted(async () => {
  await musicStore.fetchAllData()
  setTimeout(() => {
    showLoading.value = false
  }, 1200)
})

const handleSync = async () => {
  await musicStore.syncAccount()
}

const userHistory = computed(() => musicStore.recentTracks)
</script>

<template>
  <Transition name="fade">
    <LoadingScreen v-if="showLoading" />
  </Transition>

  <div class="home-2026" v-if="!showLoading">
    <header class="cinematic-hero">
      <div class="mesh-glow"></div>
      <div class="hero-content">
        <div class="status-badge">
            <Sparkles :size="14" />
            <span>AI ANALYSIS ACTIVE</span>
        </div>
        <h1 class="greeting">Hola, {{ musicStore.userProfile?.user_name || 'George' }}</h1>
        <p class="summary">
          Tu ecosistema sonoro ha evolucionado. Hemos procesado <span class="highlight">{{ musicStore.stats?.total_tracks || '0' }} canciones</span> con algoritmos DSP de última generación.
        </p>
        

        <div class="hero-actions">
          <button @click="handleSync" class="btn-glass primary" :disabled="musicStore.isSyncing">
            <Play v-if="!musicStore.isSyncing" :size="20" fill="currentColor" />
            <RefreshCcw v-else :class="{ 'spinning': musicStore.isSyncing }" :size="20" />
            <span>{{ musicStore.isSyncing ? 'Analizando...' : 'Play Insights' }}</span>
          </button>
          <button @click="router.push('/stats')" class="btn-glass secondary">
            <BarChart3 :size="20" />
            <span>Explorar DNA</span>
          </button>
        </div>
      </div>

      <div class="hero-visual">
          <div class="orbit-container">
              <div class="orbit ring-1"></div>
              <div class="orbit ring-2"></div>
              <div class="orbit ring-3"></div>
          </div>
      </div>
    </header>

    <main class="dashboard-grid">
        <section class="dna-section">
          <div class="section-top">
            <h2 class="section-title">Tu DNA Musical</h2>
            <button class="text-btn" @click="router.push('/stats')">
                Ver todo <ChevronRight :size="16" />
            </button>
          </div>
          <div class="stats-carousel">
            <StatCard
              title="Energía"
              :value="Math.round((musicStore.stats?.avg_energy || 0) * 100) + '%'"
              :percent="(musicStore.stats?.avg_energy || 0) * 100"
              :icon="Zap"
              color="#ffe100"
            />
            <StatCard
              title="Ritmo"
              :value="Math.round((musicStore.stats?.avg_danceability || 0) * 100) + '%'"
              :percent="(musicStore.stats?.avg_danceability || 0) * 100"
              :icon="Activity"
              color="#1565FF"
            />
            <StatCard
              title="Vibe"
              :value="Math.round((musicStore.stats?.avg_valence || 0) * 100) + '%'"
              :percent="(musicStore.stats?.avg_valence || 0) * 100"
              :icon="Wind"
              color="#00d4ff"
            />
          </div>
        </section>

        <div class="split-content">
          <section class="tracks-card">
            <div class="card-header">
              <h3>Descubrimiento IA</h3>
              <span class="tag">NEW RELEASES</span>
            </div>
            <div class="track-container">
              <TrackRow 
                v-for="(track, index) in musicStore.recommendations.slice(0, 6)" 
                :key="track.spotify_id" 
                :track="track" 
                :index="index + 1"
                :contextQueue="musicStore.recommendations.slice(0, 6)"
              />
            </div>
          </section>

          <section class="tracks-card">
            <div class="card-header">
              <h3>Actividad Reciente</h3>
              <span class="tag">REAL TIME</span>
            </div>
            <div class="track-container">
              <TrackRow 
                v-for="(track, index) in userHistory.slice(0, 6)" 
                :key="track.spotify_id + index" 
                :track="track" 
                :index="index + 1"
                :contextQueue="userHistory.slice(0, 6)"
              />
            </div>
          </section>
        </div>
    </main>
  </div>
</template>

<style scoped>
.home-2026 {
  display: flex;
  flex-direction: column;
  padding: 40px;
  gap: 48px;
  animation: fade-in 0.8s ease-out;
}

@keyframes fade-in {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.cinematic-hero {
  position: relative;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 60px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 32px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.mesh-glow {
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at center, rgba(21, 101, 255, 0.1) 0%, transparent 50%);
    animation: rotate 20s linear infinite;
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.hero-content {
  position: relative;
  z-index: 10;
  max-width: 600px;
}

.status-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(21, 101, 255, 0.1);
    color: var(--spotify-neon);
    padding: 6px 16px;
    border-radius: 100px;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 1px;
    margin-bottom: 24px;
    width: fit-content;
    border: 1px solid rgba(21, 101, 255, 0.2);
}

.greeting {
  font-size: 4.5rem;
  margin-bottom: 16px;
  background: linear-gradient(to bottom, #fff, #888);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.summary {
  font-size: 1.25rem;
  color: var(--spotify-text-grey);
  line-height: 1.6;
  margin-bottom: 40px;
}

.highlight {
    color: white;
    font-weight: 700;
}

.hero-actions {
  display: flex;
  gap: 20px;
}

.btn-glass {
    padding: 16px 32px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 700;
    font-size: 1rem;
    backdrop-filter: blur(10px);
}

.btn-glass.primary {
    background: white;
    color: black;
}

.btn-glass.primary:hover {
    background: var(--spotify-neon);
    transform: scale(1.05) translateY(-2px);
}

.btn-glass.secondary {
    background: rgba(255, 255, 255, 0.05);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-glass.secondary:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-2px);
}

/* Hero Visual Orbit */
.hero-visual {
    position: relative;
    width: 300px;
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.orbit-container {
    position: relative;
    width: 100%; height: 100%;
}

.orbit {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 50%;
}

.ring-1 { width: 100%; height: 100%; animation: pulse-glow 4s infinite; }
.ring-2 { width: 70%; height: 70%; border-color: rgba(21, 101, 255, 0.2); }
.ring-3 { width: 40%; height: 40%; background: radial-gradient(circle, var(--spotify-green), transparent); filter: blur(40px); opacity: 0.2; }

.dashboard-grid {
    display: flex;
    flex-direction: column;
    gap: 48px;
}

.section-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
}

.section-title {
    font-size: 2rem;
}

.text-btn {
    color: var(--spotify-text-grey);
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 4px;
}

.text-btn:hover { color: white; }

.stats-carousel {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
}

.split-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 32px;
}

.tracks-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    padding: 32px;
}

.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
}

.tag {
    font-size: 0.6rem;
    font-weight: 900;
    letter-spacing: 1px;
    color: var(--spotify-text-grey);
    border: 1px solid rgba(255,255,255,0.1);
    padding: 4px 8px;
    border-radius: 4px;
}

.track-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.spinning {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Inlined TrackRow styles */
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

@media (max-width: 1200px) {
    .split-content { grid-template-columns: 1fr; }
    .greeting { font-size: 3rem; }
    .cinematic-hero { flex-direction: column; text-align: center; padding: 40px; }
    .hero-visual { display: none; }
    .hero-actions { justify-content: center; }
    .status-badge { margin-left: auto; margin-right: auto; }
}

@media (max-width: 768px) {
    .home-2026 { padding: 20px; gap: 32px; }
    .greeting { font-size: 2.5rem; }
    .cinematic-hero { padding: 32px 20px; border-radius: 0; border: none; }
    .hero-actions { flex-direction: column; width: 100%; }
    .btn-glass { width: 100%; justify-content: center; }
    
    .track-row-2026 {
        grid-template-columns: 44px 1fr 60px;
        padding: 8px;
    }
    .album-col, .number { display: none; }
    .name { font-size: 0.9rem; }
    .artist { font-size: 0.75rem; }
    
    .stats-carousel {
        grid-template-columns: 1fr;
    }
}
</style>
