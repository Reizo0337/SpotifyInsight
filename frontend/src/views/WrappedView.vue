<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMusicStore } from '../stores/musicStore'
import { ChevronRight, ChevronLeft, Share2, Loader2 } from 'lucide-vue-next'

const musicStore = useMusicStore()
const currentSlide = ref(0)
const loading = ref(!musicStore.stats)

onMounted(async () => {
  if (!musicStore.stats) {
    loading.value = true
    await musicStore.fetchAllData()
    loading.value = false
  } else {
    loading.value = false
  }
})

const slides = computed(() => [
  { 
    title: "Tu año en música", 
    desc: `Preparado para ver tus SpotifyInsights de 2026, ${musicStore.userProfile?.user_name || 'Melómano'}?`, 
    color: "#1565FF" 
  },
  { 
    title: "Tu artista número 1", 
    desc: "No has parado de escuchar a...", 
    highlight: musicStore.stats?.top_1_artist || '...', 
    color: "#ff5e00" 
  },
  { 
    title: "Tu himno personal", 
    desc: "La canción que marcó tu ritmo este año fue", 
    highlight: musicStore.stats?.top_1_track || '...', 
    color: "#7358ff" 
  },
  { 
    title: "Tu vibra es...", 
    desc: "Tu energía musical es de un espectacular", 
    highlight: Math.round((musicStore.stats?.avg_energy || 0) * 100) + "%", 
    color: "#e8115b" 
  },
  { 
    title: "Eres un experto", 
    desc: "Has analizado profundamente", 
    highlight: (musicStore.stats?.total_tracks || 0) + " pistas", 
    color: "#1d47b9" 
  }
])

const next = () => { if (currentSlide.value < slides.value.length - 1) currentSlide.value++ }
const prev = () => { if (currentSlide.value > 0) currentSlide.value-- }
</script>

<template>
  <div v-if="loading" class="wrapped-loading">
      <Loader2 class="spinning" :size="48" />
      <p>Generando tus estadísticas...</p>
  </div>
  <div v-else class="wrapped-container" :style="{ backgroundColor: slides[currentSlide].color }">
    <div class="progress-bar-top">
      <div v-for="n in slides.length" :key="n" class="p-segment">
        <div class="p-fill" :class="{ 'active': currentSlide >= n-1 }"></div>
      </div>
    </div>

    <div class="slide-content">
      <span class="slide-title">{{ slides[currentSlide].title }}</span>
      <p class="slide-desc">{{ slides[currentSlide].desc }}</p>
      <div v-if="slides[currentSlide].highlight" class="highlight">
        {{ slides[currentSlide].highlight }}
      </div>
    </div>

    <div class="controls">
      <button @click="prev" :disabled="currentSlide === 0" class="ctrl-btn"><ChevronLeft :size="32" /></button>
      <button @click="next" v-if="currentSlide < slides.length - 1" class="ctrl-btn"><ChevronRight :size="32" /></button>
      <button v-else class="share-btn"><Share2 :size="20" /> Compartir</button>
    </div>

    <div class="background-decor">
        <div class="circle c1"></div>
        <div class="circle c2"></div>
    </div>
  </div>
</template>

<style scoped>
.wrapped-container {
  height: calc(100vh - 160px);
  border-radius: 12px;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  overflow: hidden;
  transition: background-color 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 40px;
}

.progress-bar-top {
  position: absolute;
  top: 20px;
  left: 20px;
  right: 20px;
  display: flex;
  gap: 6px;
}

.p-segment {
  flex: 1;
  height: 4px;
  background: rgba(255,255,255,0.2);
  border-radius: 2px;
}

.p-fill {
  height: 100%;
  width: 0;
  background: white;
  transition: width 0.3s;
}

.p-fill.active { width: 100%; }

.slide-content {
  text-align: center;
  z-index: 10;
  max-width: 800px;
}

.slide-title {
  font-size: 1.2rem;
  text-transform: uppercase;
  font-weight: 800;
  letter-spacing: 2px;
  opacity: 0.8;
}

.slide-desc {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 20px 0;
  line-height: 1.2;
}

.highlight {
  font-size: 5rem;
  font-weight: 900;
  text-shadow: 0 10px 30px rgba(0,0,0,0.3);
  animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes popIn {
  from { transform: scale(0.5); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.wrapped-loading {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  background: #121212;
  border-radius: 12px;
  color: var(--spotify-text-grey);
}

.spinning {
  animation: rotate 2s linear infinite;
  color: var(--spotify-green);
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.controls {
  position: absolute;
  bottom: 40px;
  left: 0; right: 0;
  display: flex;
  justify-content: center;
  gap: 40px;
  z-index: 20;
}

.ctrl-btn { color: white; cursor: pointer; opacity: 0.7; transition: opacity 0.2s; }
.ctrl-btn:hover { opacity: 1; }
.ctrl-btn:disabled { opacity: 0.2; }

.share-btn {
  background: white;
  color: black;
  padding: 12px 32px;
  border-radius: 30px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.background-decor .circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.1);
  filter: blur(60px);
}

.c1 { width: 400px; height: 400px; top: -100px; left: -100px; }
.c2 { width: 300px; height: 300px; bottom: -50px; right: -50px; }

@media (max-width: 768px) {
  .wrapped-container {
    height: calc(100vh - 100px);
    padding: 20px;
    border-radius: 0;
  }
  
  .slide-desc {
    font-size: 1.75rem;
  }
  
  .highlight {
    font-size: 3rem;
  }
  
  .controls {
    bottom: 24px;
    gap: 20px;
  }
  
  .share-btn {
    padding: 10px 24px;
    font-size: 0.9rem;
  }
}
</style>
