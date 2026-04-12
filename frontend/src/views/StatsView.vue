<script setup lang="ts">
import { onMounted, computed } from 'vue'
import axios from 'axios'
import { useMusicStore } from '../stores/musicStore'
import { useRouter } from 'vue-router'
import {
  ChevronLeft, TrendingUp, Mic2, Radio, Trophy, Award, Medal,
  Activity, Zap, Clock, Disc, Music, Sparkles, Users, Music2, Map, Milestone,
  Download
} from 'lucide-vue-next'

const musicStore = useMusicStore()
const router = useRouter()

const formatPercent = (val: number) => Math.round(val * 100) + '%'
const formatNumber = (num: number) => new Intl.NumberFormat().format(Math.round(num))
const formatViews = (n: number) => {
  if (n >= 1_000_000_000) return (n / 1_000_000_000).toFixed(1) + 'B'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

// Radar Chart Calculations (SVG)
const radarPath = computed(() => {
  const dna = musicStore.stats?.dna
  if (!dna) return ''
  const size = 140
  const center = 150
  // 4-axis radar: Energy (top), Danceability (right), Valence (bottom), Tempo (left)
  const tempoNorm = Math.min(dna.tempo / 200, 1) // normalize tempo to 0-1
  const points = [
    { x: center, y: center - (dna.energy * size) },                          // Top
    { x: center + (dna.danceability * size), y: center },                    // Right
    { x: center, y: center + (dna.valence * size) },                         // Bottom
    { x: center - (tempoNorm * size), y: center }                            // Left
  ]
  return `M ${points[0].x},${points[0].y} ` + points.map(p => `L ${p.x},${p.y}`).join(' ') + ' Z'
})

onMounted(() => {
    musicStore.fetchStats()
})

const timelineBounds = computed(() => {
    const years = musicStore.stats?.chronology?.map((p: any) => p.year) || []
    if (!years.length) return { min: 1970, max: 2026 }
    const min = Math.min(...years)
    const max = Math.max(...years)
    // Add some padding
    return { min: min - 1, max: max + 1 }
})

const getYearPos = (year: number) => {
    const { min, max } = timelineBounds.value
    const range = max - min || 1
    return ((year - min) / range) * 100
}

const displayYears = computed(() => {
    const { min, max } = timelineBounds.value
    const range = max - min
    const count = range > 10 ? 6 : range + 1
    const years = []
    for (let i = 0; i < count; i++) {
        years.push(Math.round(min + (i * range / (count - 1))))
    }
    return years
})

const handleExport = () => {
  const token = musicStore.accessToken
  const url = `http://localhost:8000/api/v1/music/export`
  
  // Download with auth
  axios.get(url, { 
    headers: { 'Authorization': `Bearer ${token}` },
    responseType: 'blob' 
  }).then(response => {
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `nebula_history_${Date.now()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }).catch(e => console.error("Export failed", e))
}
</script>

<template>
  <div class="stats-view custom-scrollbar">
    <div class="stats-container">
        <div class="top-nav">
          <button @click="router.back()" class="back-btn">
            <ChevronLeft :size="20" />
            <span>ATALAYA / VOLVER</span>
          </button>
          
          <div class="nav-actions">
            <button @click="handleExport" class="export-btn">
                <Download :size="16" />
                <span>EXP. CSV</span>
            </button>
            <router-link to="/wrapped" class="wrapped-cta glass">
               <Sparkles :size="18" />
               <span>EXPERIENCIA WRAPPED</span>
            </router-link>
          </div>
        </div>

        <header class="header">
          <div class="header-meta">ANÁLISIS DE SEÑAL // V3.0 NEBULA</div>
          <h1>Centro de Inteligencia</h1>
          <p>Decodificando tu frecuencia musical. Análisis basado en {{ musicStore.stats?.kpis?.total_plays }} pulsaciones de vida.</p>
        </header>

        <!-- KPI Grid -->
        <div class="kpi-grid">
            <div class="kpi-card glass">
                <div class="kpi-icon"><Clock :size="20" /></div>
                <div class="kpi-info">
                    <span class="k-label">LEALTAD SONORA</span>
                    <span class="k-val">{{ musicStore.stats?.kpis?.loyalty_ratio }} <small>SCORE</small></span>
                </div>
            </div>
            <div class="kpi-card glass highlight">
                <div class="kpi-icon"><Activity :size="20" /></div>
                <div class="kpi-info">
                    <span class="k-label">ENERGÍA MUSICAL</span>
                    <span class="k-val">{{ musicStore.stats?.kpis?.musical_energy }}%</span>
                </div>
                <div class="kpi-progress"><div class="kp-fill" :style="{ width: (musicStore.stats?.kpis?.musical_energy || 0) + '%' }"></div></div>
            </div>
            <div class="kpi-card glass">
                <div class="kpi-icon"><Zap :size="20" /></div>
                <div class="kpi-info">
                    <span class="k-label">DIVERSIDAD</span>
                    <span class="k-val">{{ musicStore.stats?.diversity_score }}%</span>
                </div>
            </div>
            <div class="kpi-card glass">
                <div class="kpi-icon"><Music :size="20" /></div>
                <div class="kpi-info">
                    <span class="k-label">CANCIONES ÚNICAS</span>
                    <span class="k-val">{{ musicStore.stats?.kpis?.unique_tracks }}</span>
                </div>
            </div>
        </div>

        <div class="stats-grid">
            <!-- Audio DNA Section with Radar Chart -->
            <section class="stat-section audio-dna glass">
                <div class="section-title">
                    <Activity :size="18" />
                    <span>DNA MUSICAL (RADAR)</span>
                </div>
                
                <div class="radar-container">
                  <svg viewBox="0 0 300 300" class="radar-svg">
                    <!-- Base circles -->
                    <circle cx="150" cy="150" r="150" class="r-circle" fill="none" stroke="rgba(255,255,255,0.05)" />
                    <circle cx="150" cy="150" r="100" class="r-circle" fill="none" stroke="rgba(255,255,255,0.05)" />
                    <circle cx="150" cy="150" r="50" class="r-circle" fill="none" stroke="rgba(255,255,255,0.05)" />
                    
                    <!-- Axes -->
                    <line x1="150" y1="0" x2="150" y2="300" stroke="rgba(255,255,255,0.1)" />
                    <line x1="0" y1="150" x2="300" y2="150" stroke="rgba(255,255,255,0.1)" />
                    
                    <!-- DNA Path -->
                    <path :d="radarPath" class="radar-fill" />
                  </svg>
                  
                  <div class="radar-labels">
                    <span class="rl label-top">ENERGÍA</span>
                    <span class="rl label-right">BAILE</span>
                    <span class="rl label-bottom">VALENCIA</span>
                    <span class="rl label-left">TEMPO</span>
                  </div>
                </div>

                <div class="dna-footer">
                    <div class="tempo-box">
                        <span class="t-label">RITMO PROMEDIO</span>
                        <span class="t-val">{{ Math.round(musicStore.stats?.kpis?.rhythm_stability || 0) }} <small>BPM</small></span>
                    </div>
                </div>
            </section>

            <!-- Activity Heatmap Section -->
            <section class="stat-section glass activity-section">
                <div class="section-title">
                    <Clock :size="18" />
                    <span>HEATMAP DE ACTIVIDAD (24H)</span>
                </div>
                
                <div class="heatmap-grid">
                  <div v-for="(val, hour) in musicStore.stats?.activity || []" :key="hour" 
                       class="h-cell" 
                       :style="{ opacity: 0.1 + (val / Math.max(...(musicStore.stats?.activity || [1])) * 0.9) }">
                    <span class="h-hour">{{ hour }}h</span>
                    <span class="h-val">{{ val }}</span>
                  </div>
                </div>
                
                <div class="heatmap-info">
                   <p>Tu pico de frecuencia ocurre a las <strong>{{ (musicStore.stats?.activity || []).indexOf(Math.max(...(musicStore.stats?.activity || [0]))) }}:00</strong>.</p>
                </div>
            </section>

            <!-- Genre Section -->
            <section class="stat-section glass genre-section">
                <div class="section-title">
                    <Radio :size="18" />
                    <span>GÉNEROS DOMINANTES</span>
                </div>
                <div class="genre-list">
                    <div v-for="g in musicStore.stats?.genres" :key="g.name" class="genre-row">
                        <div class="g-info">
                          <span class="g-name">{{ g.name }}</span>
                          <span class="g-count">{{ g.value }} señales</span>
                        </div>
                        <div class="g-bar">
                           <div class="g-fill" :style="{ width: (g.value / musicStore.stats?.genres[0]?.value * 100) + '%' }"></div>
                        </div>
                    </div>
                </div>
            </section>
            
            <!-- Top Artists Section -->
            <section class="stat-section glass artists-section">
                <div class="section-title">
                    <Users :size="18" />
                    <span>FRECUENCIAS REPETIDAS (TOP ARTISTAS)</span>
                </div>
                <div class="artist-list" v-if="musicStore.stats?.top_artists?.length">
                    <div v-for="(artist, i) in musicStore.stats.top_artists.slice(0, 5)" :key="artist.name" class="artist-item">
                        <div class="artist-rank">{{ i + 1 }}</div>
                        <div class="artist-avatar nebula-glow">
                            <span>{{ artist.name.charAt(0) }}</span>
                        </div>
                        <div class="artist-info">
                            <span class="a-name">{{ artist.name }}</span>
                            <span class="a-count">{{ artist.count }} pulsaciones</span>
                        </div>
                    </div>
                </div>
                <div v-else class="empty-state">No hay suficientes señales para identificar patrones de artista.</div>
            </section>

            <!-- Top Tracks Section -->
            <section class="stat-section glass top-tracks-section">
                <div class="section-title">
                    <Music2 :size="18" />
                    <span>SEÑALES DOMINANTES (TOP CANCIONES)</span>
                </div>
                <div class="top-track-list" v-if="musicStore.stats?.top_tracks?.length">
                    <div v-for="track in musicStore.stats.top_tracks.slice(0, 4)" :key="track.spotify_id" class="t-track-item">
                        <div class="t-track-thumb">
                            <img :src="track.thumbnail" alt="">
                        </div>
                        <div class="t-track-meta">
                            <span class="t-track-name">{{ track.name }}</span>
                            <span class="t-track-artist">{{ track.artist }}</span>
                        </div>
                        <div class="t-track-count">{{ track.count }}x</div>
                    </div>
                </div>
                <div v-else class="empty-state">Estableciendo conexión con el historial...</div>
            </section>

            <!-- Chronological Nebula: Point Map -->
            <section class="stat-section glass timeline-section full-width">
                <div class="section-title">
                    <Map :size="18" />
                    <span>MAPA CRONOLÓGICO: NEBULOSA TEMPORAL</span>
                </div>
                
                <div class="timeline-container" v-if="musicStore.stats?.chronology?.length">
                    <div class="timeline-sub">Explora la procedencia temporal de tus señales musicales</div>
                    
                    <div class="nebula-map">
                        <div class="nebula-axis-x">
                            <span v-for="y in displayYears" :key="y">{{ y }}</span>
                        </div>
                        
                        <div class="nebula-points">
                            <div v-for="(p, i) in musicStore.stats.chronology" 
                                 :key="i"
                                 class="nebula-point"
                                 :style="{ 
                                    left: getYearPos(p.year) + '%', 
                                    bottom: p.val + '%',
                                    animationDelay: (i * 0.05) + 's' 
                                 }">
                                <div class="p-glow"></div>
                                <div class="p-core" :style="{ backgroundImage: `url(${p.thumb})` }"></div>
                                <div class="p-hover glass">
                                    <span class="ph-name">{{ p.name }}</span>
                                    <span class="ph-year">{{ p.year }}</span>
                                </div>
                            </div>
                        </div>

                        <div class="nebula-line"></div>
                    </div>
                </div>
                <div v-else class="empty-state">
                    Sincronizando línea temporal... Reproduce más canciones para expandir la nebulosa.
                </div>
            </section>

            <!-- Fame Chart: Top 15 Column Chart -->
            <section class="stat-section glass fame-section full-width">
                <div class="section-title">
                    <Trophy :size="18" />
                    <span>FAME CHART: TOP 15 FRECUENCIAS GLOBALES</span>
                </div>
                
                <div class="column-chart-container" v-if="musicStore.stats?.fame_chart?.length">
                    <div class="chart-axis-y">
                        <span>{{ formatViews(musicStore.stats.fame_chart[0].views) }}</span>
                        <span>{{ formatViews(musicStore.stats.fame_chart[0].views / 2) }}</span>
                        <span>0</span>
                    </div>
                    
                    <div class="columns-wrapper">
                        <div v-for="(track, i) in musicStore.stats.fame_chart" 
                             :key="track.spotify_id" 
                             class="column-item"
                             :class="{ 'podium': i < 3 }">
                            
                            <div class="column-bar-glow"></div>
                            <div class="column-bar" 
                                 :style="{ height: (track.views / musicStore.stats.fame_chart[0].views * 100) + '%' }">
                                <span class="chart-rank">#{{ i + 1 }}</span>
                                <div class="column-tooltip glass">
                                    <div class="tt-thumb"><img :src="track.thumbnail" alt=""></div>
                                    <div class="tt-text">
                                        <div class="tt-name">{{ track.name }}</div>
                                        <div class="tt-artist">{{ track.artist }}</div>
                                        <div class="tt-views">{{ formatNumber(track.views) }} views</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="column-label">
                                <div class="c-thumb"><img :src="track.thumbnail" alt=""></div>
                                <span class="c-name">{{ track.name.substring(0, 10) }}...</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div v-else class="empty-state">
                    <p>Sincronizando frecuencias de fama... Reproduce canciones para activar el radar.</p>
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
  background: radial-gradient(circle at top right, rgba(99, 102, 241, 0.1), transparent 50%);
}

.stats-container {
  padding: 40px 60px;
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 40px;
  animation: viewEntry 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.wrapped-cta {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border-radius: 500px;
  font-weight: 800;
  font-size: 0.75rem;
  letter-spacing: 1px;
  background: linear-gradient(135deg, var(--nebula-primary), var(--nebula-accent));
  color: white;
  border: none;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
  transition: all 0.3s;
  cursor: pointer;
  text-decoration: none;
}

.wrapped-cta:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 0 30px rgba(99, 102, 241, 0.6);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 500px;
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--glass-border);
  color: white;
  font-weight: 800;
  font-size: 0.75rem;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s;
}

.export-btn:hover {
  background: rgba(255,255,255,0.1);
  border-color: var(--nebula-primary);
  transform: translateY(-2px);
}

@keyframes viewEntry {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--nebula-text-muted);
  font-weight: 800;
  font-size: 0.7rem;
  letter-spacing: 2px;
  transition: all 0.3s;
}
.back-btn:hover { color: white; transform: translateX(-5px); }

h1 { font-size: 3.5rem; font-weight: 900; letter-spacing: -2px; margin: 10px 0; line-height: 1; }
.header-meta { color: var(--nebula-primary); font-weight: 800; font-size: 0.75rem; letter-spacing: 4px; }
.header p { color: var(--nebula-text-dim); font-size: 1.1rem; max-width: 600px; }

/* KPI Grid */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
}
.kpi-card {
    padding: 20px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    gap: 16px;
    position: relative;
}
.kpi-card.highlight {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.05));
    border-color: rgba(99, 102, 241, 0.3);
}
.kpi-icon {
    width: 40px; height: 40px;
    border-radius: 10px;
    background: rgba(255,255,255,0.05);
    display: flex; align-items: center; justify-content: center;
    color: var(--nebula-primary);
}
.kpi-info { display: flex; flex-direction: column; }
.k-label { font-size: 0.6rem; font-weight: 800; color: var(--nebula-text-muted); letter-spacing: 1px; }
.k-val { font-size: 1.3rem; font-weight: 900; color: white; }
.k-val small { font-size: 0.7rem; opacity: 0.5; }

.kpi-progress { position: absolute; bottom: 0; left: 0; right: 0; height: 2px; background: rgba(255,255,255,0.05); }
.kp-fill { height: 100%; background: var(--nebula-primary); box-shadow: 0 0 10px var(--nebula-primary); }

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: 450px 1fr 1fr;
  gap: 24px;
}

.stat-section {
  padding: 24px;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-title {
    display: flex; align-items: center; gap: 10px;
    font-size: 0.7rem; font-weight: 900; letter-spacing: 1px; color: var(--nebula-primary);
}

/* Radar DNA */
.radar-container {
  position: relative;
  width: 100%;
  aspect-ratio: 1/1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}
.radar-svg { width: 100%; height: 100%; overflow: visible; }
.radar-fill {
  fill: rgba(99, 102, 241, 0.2);
  stroke: var(--nebula-primary);
  stroke-width: 2;
  filter: drop-shadow(0 0 8px var(--nebula-primary));
  transition: all 1s ease;
}
.radar-labels { position: absolute; top: 0; left: 0; width: 100%; height: 100%; color: var(--nebula-text-muted); font-size: 0.6rem; font-weight: 800; pointer-events: none; }
.rl { position: absolute; transform: translate(-50%, -50%); }
.label-top { top: 5%; left: 50%; }
.label-right { top: 50%; left: 95%; }
.label-bottom { top: 95%; left: 50%; }
.label-left { top: 50%; left: 5%; }

/* Heatmap */
.heatmap-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
}
.h-cell {
  aspect-ratio: 1/1;
  background: var(--nebula-primary);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}
.h-cell:hover { transform: scale(1.1); z-index: 5; box-shadow: 0 0 15px var(--nebula-primary); }
.h-hour { font-size: 0.6rem; font-weight: 800; color: white; opacity: 0.8; }
.h-val { font-size: 0.8rem; font-weight: 900; color: white; }

.heatmap-info { font-size: 0.8rem; color: var(--nebula-text-dim); text-align: center; }

/* Genre List */
.genre-list { display: flex; flex-direction: column; gap: 12px; }
.genre-row { display: flex; flex-direction: column; gap: 6px; }
.g-info { display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 700; color: white; }
.g-name { text-transform: uppercase; letter-spacing: 1px; }
.g-count { color: var(--nebula-text-muted); font-size: 0.7rem; }
.g-bar { height: 4px; background: rgba(255,255,255,0.05); border-radius: 2px; }
.g-fill { height: 100%; background: var(--nebula-primary); border-radius: 2px; box-shadow: 0 0 10px var(--nebula-primary); }

/* Top Artists */
.artists-section { grid-column: span 1; }
.artist-list { display: flex; flex-direction: column; gap: 15px; padding-top: 10px; }
.artist-item { display: flex; align-items: center; gap: 12px; }
.artist-rank { font-size: 0.8rem; font-weight: 900; color: var(--nebula-text-muted); width: 15px; }
.artist-avatar { 
    width: 40px; height: 40px; border-radius: 50%; background: var(--nebula-surface); 
    display: flex; align-items: center; justify-content: center; font-weight: 900;
    border: 1px solid var(--nebula-primary);
}
.artist-info { display: flex; flex-direction: column; }
.a-name { font-size: 0.85rem; font-weight: 800; color: white; }
.a-count { font-size: 0.7rem; color: var(--nebula-text-dim); }

/* Top Tracks */
.top-tracks-section { grid-column: span 1; }
.top-track-list { display: flex; flex-direction: column; gap: 12px; padding-top: 10px; }
.t-track-item { display: flex; align-items: center; gap: 12px; background: rgba(255,255,255,0.03); padding: 8px; border-radius: 12px; }
.t-track-thumb { width: 40px; height: 40px; border-radius: 8px; overflow: hidden; }
.t-track-thumb img { width: 100%; height: 100%; object-fit: cover; }
.t-track-meta { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.t-track-name { font-size: 0.8rem; font-weight: 800; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.t-track-artist { font-size: 0.7rem; color: var(--nebula-text-dim); }
.t-track-count { font-size: 0.75rem; font-weight: 900; color: var(--nebula-primary); }

/* Fame Chart: Column Chart Version */

.fame-section.full-width { grid-column: 1 / -1; min-height: 450px; }
.column-chart-container {
    height: 350px;
    display: flex;
    gap: 15px;
    padding: 20px 0 60px 0;
    position: relative;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.chart-axis-y {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    font-size: 0.6rem;
    font-weight: 800;
    color: var(--nebula-text-muted);
    padding-right: 15px;
    text-align: right;
    width: 50px;
}

.columns-wrapper {
    flex: 1;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 8px;
}

.column-item {
    flex: 1;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: center;
    position: relative;
}

.column-bar {
    width: 100%;
    background: linear-gradient(to top, var(--nebula-primary), var(--nebula-accent));
    border-radius: 6px 6px 0 0;
    position: relative;
    transition: all 1s cubic-bezier(0.16, 1, 0.3, 1);
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}

.column-bar:hover {
    filter: brightness(1.3);
    box-shadow: 0 0 25px var(--nebula-primary);
    transform: scaleX(1.1);
}

.column-item.podium .column-bar {
    background: linear-gradient(to top, #fbbf24, #f59e0b);
    box-shadow: 0 4px 20px rgba(251, 191, 36, 0.4);
}

.chart-rank {
    position: absolute;
    top: -25px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.75rem;
    font-weight: 900;
    color: var(--nebula-text-muted);
}

.column-label {
    position: absolute;
    bottom: -50px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
}

.c-thumb {
    width: 24px; height: 24px;
    border-radius: 5px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.1);
}
.c-thumb img { width: 100%; height: 100%; object-fit: cover; }
.c-name { font-size: 0.55rem; font-weight: 800; color: var(--nebula-text-dim); text-transform: uppercase; white-space: nowrap; }

/* Tooltip */
.column-tooltip {
    position: absolute;
    bottom: 120%;
    left: 50%;
    transform: translateX(-50%) translateY(10px);
    width: 200px;
    padding: 12px;
    display: flex;
    gap: 12px;
    opacity: 0;
    pointer-events: none;
    transition: all 0.3s;
    z-index: 100;
}

.column-bar:hover .column-tooltip {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}

.tt-thumb { width: 40px; height: 40px; border-radius: 8px; overflow: hidden; flex-shrink: 0; }
.tt-thumb img { width: 100%; height: 100%; object-fit: cover; }
.tt-text { display: flex; flex-direction: column; min-width: 0; }
.tt-name { font-size: 0.75rem; font-weight: 800; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tt-artist { font-size: 0.65rem; color: var(--nebula-text-muted); }
.tt-views { font-size: 0.7rem; font-weight: 900; color: #fbbf24; margin-top: 4px; }

.empty-state { text-align: center; padding: 60px; color: var(--nebula-text-muted); font-size: 0.9rem; }

.tempo-box { text-align: center; padding: 20px; background: rgba(0,0,0,0.2); border-radius: 12px; }
.t-val { font-size: 1.8rem; font-weight: 900; }

@media (max-width: 1400px) {
    .stats-grid { grid-template-columns: 1fr 1fr; }
    .audio-dna { grid-column: span 2; }
}

@media (max-width: 1024px) {
    .kpi-grid { grid-template-columns: repeat(2, 1fr); }
    .stats-container { padding: 30px; }
}

@media (max-width: 768px) {
    .stats-grid { grid-template-columns: 1fr; }
    .audio-dna { grid-column: span 1; }
    h1 { font-size: 2.5rem; }
}
/* Chronological Nebula */
.timeline-section { min-height: 500px; }
.timeline-sub { font-size: 0.8rem; color: var(--nebula-text-muted); margin-bottom: 30px; letter-spacing: 1px; }

.nebula-map {
    height: 300px;
    position: relative;
    margin: 40px 20px;
    background: radial-gradient(circle at center, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
    border-left: 1px solid rgba(255,255,255,0.05);
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.nebula-axis-x {
    position: absolute; bottom: -30px; width: 100%;
    display: flex; justify-content: space-between;
    font-size: 0.6rem; font-weight: 800; color: var(--nebula-text-muted);
    letter-spacing: 3px;
}

.nebula-line {
    position: absolute; bottom: 0; left: 0; width: 100%; height: 1px;
    background: linear-gradient(90deg, transparent, var(--nebula-primary), transparent);
    opacity: 0.3;
}

.nebula-points { position: absolute; inset: 0; }

.nebula-point {
    position: absolute;
    width: 12px; height: 12px;
    transform: translate(-50%, 50%);
    cursor: pointer;
    z-index: 10;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    animation: pointPop 0.6s backwards;
}

@keyframes pointPop {
    from { transform: translate(-50%, 50%) scale(0); opacity: 0; }
    to { transform: translate(-50%, 50%) scale(1); opacity: 1; }
}

.p-core {
    width: 100%; height: 100%; border-radius: 50%;
    background-size: cover; background-position: center;
    border: 1.5px solid white;
    box-shadow: 0 0 10px rgba(255,255,255,0.3);
}

.p-glow {
    position: absolute; inset: -4px;
    background: var(--nebula-primary);
    filter: blur(8px);
    border-radius: 50%;
    opacity: 0.4;
    transition: opacity 0.3s;
}

.nebula-point:hover { z-index: 100; transform: translate(-50%, 50%) scale(2.5); }
.nebula-point:hover .p-glow { opacity: 0.9; inset: -8px; }

.p-hover {
    position: absolute; bottom: calc(100% + 15px); left: 50%;
    transform: translateX(-50%);
    padding: 8px 12px; border-radius: 8px;
    width: max-content; max-width: 150px;
    opacity: 0; pointer-events: none;
    transition: all 0.2s;
    text-align: center;
}

.nebula-point:hover .p-hover { opacity: 1; bottom: calc(100% + 10px); }

.ph-name { display: block; font-size: 0.7rem; font-weight: 800; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ph-year { display: block; font-size: 0.6rem; color: var(--nebula-primary); font-weight: 900; margin-top: 2px; }

.timeline-labels {
    position: absolute; bottom: 40px; left: 60px; right: 60px;
    display: flex; justify-content: space-between;
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem; color: var(--nebula-text-muted);
}

</style>
