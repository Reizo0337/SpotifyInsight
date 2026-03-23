<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useMusicStore } from '../stores/musicStore'
import StatCard from '../components/StatCard.vue'
import TrackRow from '../components/TrackRow.vue'
import { 
  RefreshCcw, Zap, BarChart3, 
  Wind, Activity, 
  ChevronRight, Play, Sparkles
} from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const musicStore = useMusicStore()
const router = useRouter()

onMounted(async () => {
  if (musicStore.accessToken) {
    await musicStore.fetchAllData()
  }
})

const handleSync = async () => {
  await musicStore.syncAccount()
}

const userHistory = computed(() => musicStore.recentTracks)
</script>

<template>
  <div class="home-nebula">
    <header class="cinematic-hero">
      <!-- Ambient Glow Blobs -->
      <div class="blob b1"></div>
      <div class="blob b2"></div>
      
      <div class="hero-content">
        <div class="status-badge">
            <Sparkles :size="14" />
            <span>SISTEMA NEBULA ACTIVO</span>
        </div>
        <h1 class="greeting">Bienvenido, {{ musicStore.userProfile?.username || 'Viajero' }}</h1>
        <p class="summary">
          Tu universo musical está listo. Hemos analizado <span class="highlight">{{ musicStore.stats?.total_tracks || '0' }} señales</span> únicas en tu trayectoria estelar.
        </p>
        

        <div class="hero-actions">
          <button v-if="!musicStore.isSpotifyConnected" @click="musicStore.connectSpotify" class="btn-nebula primary">
            <Sparkles :size="20" />
            <span>Conectar Spotify</span>
          </button>
          <button v-else @click="handleSync" class="btn-nebula primary" :disabled="musicStore.isSyncing">
            <Play v-if="!musicStore.isSyncing" :size="20" fill="currentColor" />
            <RefreshCcw v-else :class="{ 'spinning': musicStore.isSyncing }" :size="20" />
            <span>{{ musicStore.isSyncing ? 'Analizando...' : 'Sincronizar Spotify' }}</span>
          </button>
          <button @click="router.push('/stats')" class="btn-nebula secondary">
            <BarChart3 :size="20" />
            <span>Ver Análisis DNA</span>
          </button>
        </div>
      </div>

      <div class="hero-visual">
          <div class="core-nebula">
              <div class="core-glow"></div>
              <div class="core-rings">
                  <div class="ring r1"></div>
                  <div class="ring r2"></div>
                  <div class="ring r3"></div>
              </div>
          </div>
      </div>
    </header>

    <main class="dashboard-grid">
        <section class="dna-section">
          <div class="section-top">
            <h2 class="section-title">Tu Biometría Musical</h2>
            <button class="text-btn" @click="router.push('/stats')">
                Ver Detalles <ChevronRight :size="16" />
            </button>
          </div>
          <div class="stats-carousel">
            <StatCard
              title="Energía"
              :value="Math.round((musicStore.stats?.avg_energy || 0) * 100) + '%'"
              :percent="(musicStore.stats?.avg_energy || 0) * 100"
              :icon="Zap"
              color="var(--nebula-primary)"
            />
            <StatCard
              title="Ritmo"
              :value="Math.round((musicStore.stats?.avg_danceability || 0) * 100) + '%'"
              :percent="(musicStore.stats?.avg_danceability || 0) * 100"
              :icon="Activity"
              color="var(--nebula-accent)"
            />
            <StatCard
              title="Vibe"
              :value="Math.round((musicStore.stats?.avg_valence || 0) * 100) + '%'"
              :percent="(musicStore.stats?.avg_valence || 0) * 100"
              :icon="Wind"
              color="#818cf8"
            />
          </div>
        </section>

        <div class="split-content">
          <section class="tracks-card glass">
            <div class="card-header">
              <h3>Sugerencias Estelares</h3>
              <span class="tag">NEBULA AI</span>
            </div>
            <div class="track-container">
              <TrackRow 
                v-for="(track, index) in musicStore.recommendations.slice(0, 6)" 
                :key="track.spotify_id" 
                :track="track" 
                :index="Number(index) + 1"
                :contextQueue="musicStore.recommendations.slice(0, 6)"
              />
              <div v-if="musicStore.recommendations.length === 0" class="empty-state">
                Inicia la sincronización para recibir sugerencias
              </div>
            </div>
          </section>

          <section class="tracks-card glass">
            <div class="card-header">
              <h3>Trayectoria Reciente</h3>
              <span class="tag">REAL TIME</span>
            </div>
            <div class="track-container">
              <TrackRow 
                v-for="(track, index) in userHistory.slice(0, 6)" 
                :key="track.spotify_id + index" 
                :track="track" 
                :index="Number(index) + 1"
                :contextQueue="userHistory.slice(0, 6)"
              />
              <div v-if="userHistory.length === 0" class="empty-state">
                No hay actividad reciente detectada
              </div>
            </div>
          </section>
        </div>
    </main>
  </div>
</template>

<style scoped>
.home-nebula {
  display: flex;
  flex-direction: column;
  padding: 40px;
  gap: 60px;
  animation: fade-in 1s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes fade-in {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

.cinematic-hero {
  position: relative;
  min-height: 460px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 60px 80px;
  background: var(--nebula-surface);
  border-radius: 40px;
  overflow: hidden;
  border: 1px solid var(--glass-border);
  backdrop-filter: var(--glass-blur);
  box-shadow: 0 40px 100px rgba(0,0,0,0.4);
}

/* Hero Blobs */
.blob {
    position: absolute;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    filter: blur(100px);
    opacity: 0.15;
    z-index: 1;
}
.b1 { background: var(--nebula-primary); top: -100px; left: -100px; }
.b2 { background: var(--nebula-accent); bottom: -100px; right: -100px; }

.hero-content {
  position: relative;
  z-index: 10;
  max-width: 650px;
}

.status-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(99, 102, 241, 0.1);
    color: var(--nebula-primary);
    padding: 10px 20px;
    border-radius: 500px;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 32px;
    width: fit-content;
    border: 1px solid rgba(99, 102, 241, 0.2);
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.1);
}

.greeting {
  font-size: 4.5rem;
  font-weight: 800;
  letter-spacing: -3px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.1;
}

.summary {
  font-size: 1.25rem;
  color: var(--nebula-text-dim);
  line-height: 1.6;
  margin-bottom: 48px;
  font-weight: 300;
}

.highlight {
    color: white;
    font-weight: 600;
    text-shadow: 0 0 15px rgba(255,255,255,0.3);
}

.btn-nebula {
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: none;
}

.btn-nebula.primary {
    background: white;
    color: black;
    box-shadow: 0 20px 40px rgba(255, 255, 255, 0.1);
}

.btn-nebula.primary:hover {
    background: var(--nebula-primary);
    color: white;
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 20px 40px rgba(99, 102, 241, 0.3);
}

.btn-nebula.secondary {
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: white;
    background: rgba(255, 255, 255, 0.02);
}

.btn-nebula.secondary:hover {
    background: rgba(255, 255, 255, 0.06);
    transform: translateY(-4px);
}

/* Cinematic Visual */
.hero-visual {
    width: 400px;
    height: 400px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    perspective: 1000px;
}

.core-nebula {
    width: 120px;
    height: 120px;
    position: relative;
}

.core-glow {
    position: absolute;
    width: 100%; height: 100%;
    background: radial-gradient(circle, var(--nebula-primary), var(--nebula-accent));
    filter: blur(40px);
    opacity: 0.6;
    animation: core-breath 4s ease-in-out infinite;
}

.ring {
    position: absolute;
    top: 50%; left: 50%;
    transform-style: preserve-3d;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    animation: rotate-ring 10s linear infinite;
}

.r1 { width: 300px; height: 300px; margin-top: -150px; margin-left: -150px; animation-duration: 25s; }
.r2 { width: 400px; height: 120px; margin-top: -60px; margin-left: -200px; animation-duration: 15s; border-color: rgba(34, 211, 238, 0.2); }
.r3 { width: 150px; height: 400px; margin-top: -200px; margin-left: -75px; animation-duration: 40s; border-color: rgba(99, 102, 241, 0.1); }

@keyframes core-breath {
    0%, 100% { transform: scale(1); opacity: 0.6; }
    50% { transform: scale(1.2); opacity: 0.8; }
}

@keyframes rotate-ring {
    from { transform: rotateX(60deg) rotateZ(0deg); }
    to { transform: rotateX(60deg) rotateZ(360deg); }
}

.dashboard-grid {
    display: flex;
    flex-direction: column;
    gap: 60px;
}

.section-title {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -1px;
}

.split-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 40px;
}

.spinning { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 1400px) {
    .greeting { font-size: 3.5rem; }
    .hero-visual { width: 300px; height: 300px; }
}

@media (max-width: 1200px) {
    .split-content { grid-template-columns: 1fr; }
    .cinematic-hero { flex-direction: column; text-align: center; padding: 60px 40px; }
    .hero-visual { margin-top: 40px; }
    .hero-actions { justify-content: center; }
    .status-badge { margin-left: auto; margin-right: auto; }
}

@media (max-width: 768px) {
    .home-nebula { padding: 24px; }
    .greeting { font-size: 2.8rem; }
    .hero-actions { flex-direction: column; }
    .btn-nebula { width: 100%; justify-content: center; }
}
</style>
