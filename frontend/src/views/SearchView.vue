<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useMusicStore } from '../stores/musicStore'
import { Search as SearchIcon, Loader2, Sparkles, Orbit, Radio, History, Zap, BarChart3, ChevronRight } from 'lucide-vue-next'
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

const categories = [
  { id: 'core', name: 'Núcleo Central', icon: Orbit, color: 'var(--nebula-primary)', desc: 'Tus señales más fuertes' },
  { id: 'puns', name: 'Pulso Galáctico', icon: Zap, color: 'var(--nebula-accent)', desc: 'Lo más escuchado ahora' },
  { id: 'radio', name: 'Radio Telescopio', icon: Radio, color: '#f59e0b', desc: 'Emisiones infinitas' },
  { id: 'stats', name: 'Análisis DNA', icon: BarChart3, color: '#ec4899', desc: 'Tu trayectoria estelar' }
]

const recentSignals = computed(() => musicStore.recentTracks.slice(0, 8))
</script>

<template>
  <div class="search-nebula">
    <header class="search-header">
      <div class="search-oracle glass">
        <SearchIcon :size="20" class="oracle-icon" />
        <input 
          v-model="query" 
          type="text" 
          placeholder="Rastrear señales en el cosmos..." 
          autofocus
        />
        <div v-if="musicStore.isLoading" class="oracle-loading">
            <Loader2 :size="20" class="spin" />
        </div>
      </div>
    </header>

    <div v-if="query" class="results-nebula animate-in">
        <div class="results-header">
            <Sparkles :size="16" />
            <span>RESULTADOS: "{{ query.toUpperCase() }}"</span>
        </div>
        
        <div class="results-grid single-column">
            <div class="result-section glass">
                <div class="s-header">
                    <Sparkles :size="18" />
                    <h3>SEÑALES DETECTADAS</h3>
                </div>
                <div class="track-list-nebula">
                    <TrackRow 
                        v-for="track in musicStore.searchResults" 
                        :key="track.id || track.spotify_id" 
                        :track="track"
                        :contextQueue="musicStore.searchResults"
                    />
                    <div v-if="!musicStore.isLoading && musicStore.searchResults.length === 0" class="empty-hint">Sin señales en esta frecuencia</div>
                </div>
            </div>
        </div>
    </div>

    <main v-else class="explore-nebula animate-in">
        <section class="sectors-section">
            <h2 class="section-title">Sectores de Exploración</h2>
            <div class="sectors-grid">
                <div v-for="cat in categories" :key="cat.id" class="sector-card glass" :style="{ '--accent': cat.color }">
                    <div class="sector-icon">
                        <component :is="cat.icon" :size="28" />
                    </div>
                    <div class="sector-info">
                        <span class="sector-name">{{ cat.name }}</span>
                        <span class="sector-desc">{{ cat.desc }}</span>
                    </div>
                    <ChevronRight :size="16" class="sector-arrow" />
                    <div class="sector-glow"></div>
                </div>
            </div>
        </section>

        <section class="recent-signals" v-if="recentSignals.length > 0">
            <div class="section-top">
                <div class="title-with-icon">
                    <History :size="20" />
                    <h2 class="section-title">Últimas Trayectorias</h2>
                </div>
                <button class="text-btn">EXPANDIR TODO</button>
            </div>
            <div class="recent-grid-nebula">
               <TrackRow 
                v-for="(track, index) in recentSignals" 
                :key="track.spotify_id + index" 
                :track="track"
                :index="Number(index) + 1"
                :showPlayedAt="true"
                :contextQueue="recentSignals"
              />
            </div>
        </section>
    </main>
  </div>
</template>

<style scoped>
.search-nebula {
    padding: 40px;
    display: flex;
    flex-direction: column;
    gap: 48px;
    animation: fade-up 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes fade-up {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.search-header {
    position: sticky;
    top: 40px;
    z-index: 100;
}

.search-oracle {
    max-width: 600px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 18px 24px;
    border-radius: 20px;
    box-shadow: 0 30px 60px rgba(0,0,0,0.4);
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.search-oracle:focus-within {
    transform: scale(1.02);
    border-color: var(--nebula-primary);
    box-shadow: 0 40px 80px rgba(99, 102, 241, 0.2);
}

.oracle-icon { color: var(--nebula-text-muted); }

input {
    flex: 1;
    background: transparent;
    border: none;
    color: white;
    font-size: 1.1rem;
    font-weight: 500;
}

input:focus { outline: none; }
input::placeholder { color: var(--nebula-text-muted); opacity: 0.5; }

.oracle-loading { color: var(--nebula-primary); }

.results-nebula { display: flex; flex-direction: column; gap: 32px; }

.results-header {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.7rem; font-weight: 800; letter-spacing: 2px;
    color: var(--nebula-primary);
    background: rgba(99, 102, 241, 0.05);
    padding: 8px 16px; border-radius: 500px;
    width: fit-content;
}

.results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 24px;
}

.result-section { border-radius: 24px; padding: 24px; height: 100%; }

.s-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    color: var(--nebula-text-muted);
}

.s-header h3 { 
    font-size: 0.8rem; 
    font-weight: 800; 
    margin-bottom: 0 !important; 
    letter-spacing: 1px; 
}

.track-list-nebula { display: flex; flex-direction: column; gap: 4px; }
.empty-hint { font-size: 0.85rem; color: var(--nebula-text-muted); opacity: 0.5; text-align: center; padding: 40px; }

.sectors-section { display: flex; flex-direction: column; gap: 24px; }
.section-title { font-size: 1.8rem; font-weight: 800; letter-spacing: -1px; }

.sectors-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 24px;
}

.sector-card {
    padding: 24px;
    border-radius: 24px;
    display: flex;
    align-items: center;
    gap: 20px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: all 0.3s;
}

.sector-card:hover {
    transform: translateY(-8px);
    background: rgba(255, 255, 255, 0.06);
}

.sector-icon {
    width: 60px; height: 60px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.03);
    display: flex; align-items: center; justify-content: center;
    color: var(--accent);
    border: 1px solid rgba(255,255,255,0.05);
}

.sector-info { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.sector-name { font-size: 1.1rem; font-weight: 700; color: white; }
.sector-desc { font-size: 0.8rem; color: var(--nebula-text-muted); font-weight: 500; }

.sector-arrow { opacity: 0; transform: translateX(-10px); transition: all 0.3s; color: var(--nebula-text-muted); }
.sector-card:hover .sector-arrow { opacity: 1; transform: translateX(0); }

.sector-glow {
    position: absolute; bottom: -20px; right: -20px;
    width: 80px; height: 80px;
    background: var(--accent);
    filter: blur(40px);
    opacity: 0.1;
}

.recent-signals { display: flex; flex-direction: column; gap: 24px; margin-top: 40px; }
.section-top { display: flex; align-items: center; justify-content: space-between; }
.title-with-icon { display: flex; align-items: center; gap: 12px; color: var(--nebula-primary); }

.recent-grid-nebula { display: flex; flex-direction: column; gap: 8px; }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 1200px) {
    .results-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
    .search-nebula { padding: 24px; }
    .search-oracle { padding: 14px 18px; }
    .sectors-grid { grid-template-columns: 1fr; }
    .section-title { font-size: 1.4rem; }
}
</style>
