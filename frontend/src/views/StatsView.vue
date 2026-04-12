<script setup lang="ts">
import { onMounted } from 'vue'
import { useMusicStore } from '../stores/musicStore'
import { useRouter } from 'vue-router'
import {
  ChevronLeft, TrendingUp, Mic2, Radio, Trophy, Award, Medal,
  Activity, Zap, Clock, Disc, Music
} from 'lucide-vue-next'
import StatCard from '../components/StatCard.vue'

const musicStore = useMusicStore()
const router = useRouter()

const formatPercent = (val: number) => Math.round(val * 100) + '%'
const formatNumber = (num: number) => new Intl.NumberFormat().format(Math.round(num))

const getTrophyColor = (index: number) => {
  if (index === 0) return '#b9f2ff' // Diamond
  if (index === 1) return '#ffd700' // Gold
  if (index === 2) return '#cd7f32' // Bronze
  return 'transparent'
}

const getRankIcon = (index: number) => {
  if (index === 0) return Trophy
  if (index === 1) return Award
  if (index === 2) return Medal
  return null
}

onMounted(() => {
    musicStore.fetchTopData()
    musicStore.fetchAllData()
})
</script>

<template>
  <div class="stats-view custom-scrollbar">
    <div class="stats-container">
        <button @click="router.back()" class="back-btn">
        <ChevronLeft :size="20" />
        <span>RECEPTOR / ATRÁS</span>
        </button>

        <header class="header">
        <div class="header-meta">SIGNAL ANALYSIS // V2.1</div>
        <h1>Centro de Inteligencia</h1>
        <p>Decodificando tu frecuencia musical. Análisis basado en {{ musicStore.stats?.total_listened }} puntos de señal.</p>
        </header>

        <!-- KPI Grid -->
        <div class="kpi-grid">
            <div class="kpi-card glass">
                <div class="kpi-icon"><Clock :size="24" /></div>
                <div class="kpi-info">
                    <span class="k-label">TIEMPO TOTAL</span>
                    <span class="k-val">{{ formatNumber(musicStore.stats?.total_playtime_min || 0) }} <small>MIN</small></span>
                </div>
            </div>
            <div class="kpi-card glass highlight">
                <div class="kpi-icon"><Activity :size="24" /></div>
                <div class="kpi-info">
                    <span class="k-label">INTENSIDAD VIBE</span>
                    <span class="k-val">{{ Math.round((musicStore.stats?.vibe_intensity || 0) * 100) }}%</span>
                </div>
                <div class="kpi-progress"><div class="kp-fill" :style="{ width: (musicStore.stats?.vibe_intensity * 100 || 0) + '%' }"></div></div>
            </div>
            <div class="kpi-card glass">
                <div class="kpi-icon"><Zap :size="24" /></div>
                <div class="kpi-info">
                    <span class="k-label">ENGAGEMENT</span>
                    <span class="k-val">{{ Math.round(musicStore.stats?.engagement_score || 0) }}%</span>
                </div>
            </div>
            <div class="kpi-card glass">
                <div class="kpi-icon"><Music :size="24" /></div>
                <div class="kpi-info">
                    <span class="k-label">CATÁLOGO</span>
                    <span class="k-val">{{ musicStore.stats?.total_tracks }} <small>TRACKS</small></span>
                </div>
            </div>
        </div>

        <div class="stats-grid">
            <!-- Audio DNA Section -->
            <section class="stat-section audio-dna glass">
                <div class="section-title">
                    <Activity :size="20" />
                    <span>DNA MUSICAL</span>
                </div>
                <div class="dna-bars">
                    <div class="dna-row" v-for="(val, key) in {
                        'Energía': musicStore.stats?.avg_energy,
                        'Bailabilidad': musicStore.stats?.avg_danceability,
                        'Valencia': musicStore.stats?.avg_valence,
                        'Popularidad': (musicStore.stats?.avg_popularity || 0) / 100
                    }" :key="key">
                        <div class="dna-info">
                            <span class="dna-label">{{ key }}</span>
                            <span class="dna-val">{{ formatPercent(val || 0) }}</span>
                        </div>
                        <div class="dna-bar-bg">
                            <div class="dna-bar-fill" :style="{ width: formatPercent(val || 0) }"></div>
                        </div>
                    </div>
                    <div class="dna-footer">
                        <div class="tempo-box">
                            <span class="t-label">TEMPO MEDIO</span>
                            <span class="t-val">{{ Math.round(musicStore.stats?.avg_tempo || 0) }} <small>BPM</small></span>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Genre Section -->
            <section class="stat-section glass genre-section">
                <div class="section-title">
                    <Radio :size="20" />
                    <span>AFINIDAD DE GÉNERO</span>
                </div>
                <div class="genre-cloud">
                    <div v-for="g in musicStore.stats?.top_genres" :key="g.name" class="genre-tag">
                        <span class="g-name">{{ g.name }}</span>
                        <span class="g-count">{{ g.count }}</span>
                    </div>
                </div>
            </section>

            <!-- Top Artists Section -->
            <section class="stat-section glass">
                <div class="section-title">
                    <Mic2 :size="20" />
                    <span>FUENTES DE SEÑAL TOP</span>
                </div>
                <div class="ranking-list">
                    <div v-for="(artist, i) in musicStore.topArtists" :key="i" class="rank-item" :class="'rank-' + (Number(i) + 1)">
                        <div class="rank-left">
                            <span class="rank-idx">{{ i + 1 }}</span>
                            <div class="rank-img">
                                <img :src="artist.thumbnail || `https://api.dicebear.com/7.x/initials/svg?seed=${artist.artist}`" alt="">
                            </div>
                            <span class="rank-name">{{ artist.artist }}</span>
                        </div>
                        <div class="rank-right">
                            <span class="rank-count">{{ artist.play_count }} <small>PLAYS</small></span>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Top Tracks Section -->
            <section class="stat-section glass">
                <div class="section-title">
                    <Disc :size="20" />
                    <span>FRECUENCIAS RESONANTES</span>
                </div>
                <div class="ranking-list">
                    <div v-for="(track, i) in musicStore.topTracks" :key="i" class="rank-item track-item">
                        <div class="rank-left">
                            <span class="rank-idx">{{ i + 1 }}</span>
                            <div class="rank-img mini">
                                <img :src="track.thumbnail" alt="">
                            </div>
                            <div class="track-meta">
                                <span class="t-name">{{ track.track_name }}</span>
                                <span class="t-artist">{{ track.artist }}</span>
                            </div>
                        </div>
                        <div class="rank-right">
                            <div class="play-pill">{{ track.play_count }}</div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </div>
  </div>
</template>

<style scoped>
.stats-view {
  height: 100%;
  overflow-y: auto;
  background: radial-gradient(circle at top right, rgba(99, 102, 241, 0.05), transparent 40%);
}

.stats-container {
  padding: 60px 80px;
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 60px;
  animation: viewEntry 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes viewEntry {
    from { opacity: 0; transform: translateY(30px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--nebula-text-muted);
  font-weight: 800;
  font-size: 0.7rem;
  letter-spacing: 2px;
  width: fit-content;
  transition: all 0.3s;
}
.back-btn:hover { color: white; transform: translateX(-8px); }

h1 { font-size: 4rem; font-weight: 900; letter-spacing: -3px; margin: 10px 0; line-height: 1; }
.header-meta { color: var(--nebula-primary); font-weight: 800; font-size: 0.75rem; letter-spacing: 4px; }
.header p { color: var(--nebula-text-dim); font-size: 1.2rem; max-width: 600px; }

/* KPI Grid */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;
}
.kpi-card {
    padding: 24px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    gap: 20px;
    position: relative;
    overflow: hidden;
}
.kpi-card.highlight {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
    border-color: rgba(99, 102, 241, 0.3);
}
.kpi-icon {
    width: 48px; height: 48px;
    border-radius: 12px;
    background: rgba(255,255,255,0.05);
    display: flex; align-items: center; justify-content: center;
    color: var(--nebula-primary);
}
.kpi-info { display: flex; flex-direction: column; gap: 4px; }
.k-label { font-size: 0.65rem; font-weight: 800; color: var(--nebula-text-muted); letter-spacing: 1px; }
.k-val { font-size: 1.5rem; font-weight: 900; color: white; }
.k-val small { font-size: 0.8rem; opacity: 0.5; }

.kpi-progress { position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: rgba(255,255,255,0.05); }
.kp-fill { height: 100%; background: var(--nebula-primary); box-shadow: 0 0 10px var(--nebula-primary); }

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: 450px 1fr 1fr;
  gap: 32px;
  align-items: start;
}

.stat-section {
  padding: 32px;
  border-radius: 24px;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.section-title {
    display: flex; align-items: center; gap: 12px;
    font-size: 0.75rem; font-weight: 900; letter-spacing: 2px; color: var(--nebula-primary);
}

/* Audio DNA */
.dna-bars { display: flex; flex-direction: column; gap: 24px; }
.dna-row { display: flex; flex-direction: column; gap: 10px; }
.dna-info { display: flex; justify-content: space-between; align-items: center; }
.dna-label { font-size: 0.85rem; font-weight: 700; color: white; }
.dna-val { font-size: 1rem; font-weight: 900; color: var(--nebula-primary); }
.dna-bar-bg { height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden; }
.dna-bar-fill {
    height: 100%; background: linear-gradient(90deg, var(--nebula-primary), var(--nebula-accent));
    border-radius: 3px; transition: width 1s cubic-bezier(0.16, 1, 0.3, 1);
}

.tempo-box {
    margin-top: 20px;
    padding: 24px;
    background: rgba(255,255,255,0.02);
    border-radius: 16px;
    border: 1px solid var(--glass-border);
    text-align: center;
}
.t-label { display: block; font-size: 0.65rem; font-weight: 800; color: var(--nebula-text-muted); margin-bottom: 5px; }
.t-val { font-size: 2rem; font-weight: 900; color: white; text-shadow: 0 0 20px rgba(255,255,255,0.2); }

/* Ranking Lists */
.ranking-list { display: flex; flex-direction: column; gap: 12px; }
.rank-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px; border-radius: 16px; transition: all 0.3s;
    border: 1px solid transparent;
}
.rank-item:hover { background: rgba(255,255,255,0.03); border-color: var(--glass-border); transform: translateX(5px); }

.rank-left { display: flex; align-items: center; gap: 16px; }
.rank-idx { font-size: 0.8rem; font-weight: 900; color: var(--nebula-text-muted); width: 20px; }
.rank-img { width: 44px; height: 44px; border-radius: 10px; overflow: hidden; border: 1px solid var(--glass-border); }
.rank-img.mini { width: 36px; height: 36px; }
.rank-img img { width: 100%; height: 100%; object-fit: cover; }
.rank-name { font-weight: 700; color: white; font-size: 1rem; }

.rank-count { font-weight: 800; color: var(--nebula-primary); font-size: 0.9rem; }
.rank-count small { font-size: 0.6rem; opacity: 0.6; }

.track-meta { display: flex; flex-direction: column; }
.t-name { font-weight: 700; color: white; font-size: 0.9rem; }
.t-artist { font-size: 0.75rem; color: var(--nebula-text-muted); }

.play-pill {
    padding: 4px 10px;
    background: rgba(99, 102, 241, 0.1);
    color: var(--nebula-primary);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 800;
}

/* Genre Cloud */
.genre-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}
.genre-tag {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--glass-border);
    padding: 8px 16px;
    border-radius: 30px;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.3s;
}
.genre-tag:hover {
    background: var(--nebula-primary);
    border-color: var(--nebula-primary);
    transform: translateY(-3px);
}
.g-name { font-size: 0.8rem; font-weight: 700; color: white; text-transform: uppercase; letter-spacing: 1px; }
.g-count { font-size: 0.7rem; font-weight: 900; color: var(--nebula-text-dim); background: rgba(0,0,0,0.2); padding: 2px 6px; border-radius: 6px; }
.genre-tag:hover .g-count { color: white; background: rgba(255,255,255,0.2); }

/* Rank specific styles */
.rank-1 .rank-name { color: var(--nebula-accent); }
.rank-1 .rank-idx { color: var(--nebula-accent); }

@media (max-width: 1400px) {
    .stats-grid { grid-template-columns: 1fr 1fr; }
    .audio-dna { grid-column: span 2; }
}

@media (max-width: 1024px) {
    .kpi-grid { grid-template-columns: repeat(2, 1fr); }
    .stats-container { padding: 40px; }
}

@media (max-width: 768px) {
    .kpi-grid { grid-template-columns: 1fr; }
    .stats-grid { grid-template-columns: 1fr; }
    .audio-dna { grid-column: span 1; }
    h1 { font-size: 2.5rem; }
}
</style>
