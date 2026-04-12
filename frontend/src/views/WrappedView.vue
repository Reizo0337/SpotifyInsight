<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMusicStore } from '../stores/musicStore'
import { useRouter } from 'vue-router'
import { ChevronRight, ChevronLeft, Share2, Loader2, X, Sparkles } from 'lucide-vue-next'

const musicStore = useMusicStore()
const router = useRouter()
const currentSlide = ref(0)
const loading = ref(true)

const fetchWrappedData = async () => {
  loading.value = true
  // Force fetch with wrapped=true to get the story metadata
  await musicStore.fetchStats(true)
  loading.value = false
}

onMounted(() => {
  fetchWrappedData()
})

const storyBlocks = computed(() => musicStore.stats?.wrapped?.story_blocks || [])

const next = () => { 
  if (currentSlide.value < storyBlocks.value.length - 1) {
    currentSlide.value++ 
  } else {
    router.push('/stats')
  }
}
const prev = () => { if (currentSlide.value > 0) currentSlide.value-- }

// Dynamic background based on slide index
const getSlideBg = (idx: number) => {
  const colors = [
    'linear-gradient(135deg, #6366f1, #a855f7)', // Indigo/Purple
    'linear-gradient(135deg, #10b981, #3b82f6)', // Emerald/Blue
    'linear-gradient(135deg, #f59e0b, #ef4444)', // Amber/Red
    'linear-gradient(135deg, #ec4899, #8b5cf6)'  // Pink/Violet
  ]
  return colors[idx % colors.length]
}
</script>

<template>
  <div class="wrapped-experience">
    <!-- Loading State -->
    <div v-if="loading" class="wrapped-loading">
        <div class="loader-content">
          <Loader2 class="spinning" :size="48" />
          <h2>SINCRONIZANDO RECUERDOS...</h2>
          <p>Nebula está decodificando tus frecuencias más intensas.</p>
        </div>
    </div>

    <!-- Story Container -->
    <div v-else-if="storyBlocks.length" class="story-container" :style="{ background: getSlideBg(currentSlide) }">
      <!-- Progress Bar -->
      <div class="progress-bar-container">
        <div v-for="n in storyBlocks.length" :key="n" class="p-segment">
          <div class="p-fill" :class="{ 'active': currentSlide >= n-1, 'current': currentSlide === n-1 }"></div>
        </div>
      </div>

      <button @click="router.push('/stats')" class="close-btn"><X :size="24" /></button>

      <!-- Slide content -->
      <Transition name="slide-fade" mode="out-in">
        <div :key="currentSlide" class="slide-content">
          <div class="slide-header">
             <Sparkles v-if="currentSlide === 0" :size="32" class="sparkle-icon" />
             <span class="slide-meta">{{ storyBlocks[currentSlide].title }}</span>
          </div>

          <h2 class="slide-text">{{ storyBlocks[currentSlide].text }}</h2>
          
          <div v-if="storyBlocks[currentSlide].highlight" class="slide-highlight">
            {{ storyBlocks[currentSlide].highlight }}
          </div>

          <!-- Dynamic Visualizers based on type -->
          <div v-if="storyBlocks[currentSlide].type === 'radar'" class="visual-extra">
             <div class="mini-sonar"></div>
          </div>
        </div>
      </Transition>

      <!-- Touch areas -->
      <div class="touch-zones">
        <div @click="prev" class="zone left"></div>
        <div @click="next" class="zone right"></div>
      </div>

      <!-- Controls -->
      <div class="controls">
        <button @click="prev" :disabled="currentSlide === 0" class="ctrl-btn"><ChevronLeft :size="32" /></button>
        <button @click="next" class="ctrl-btn">
          <ChevronRight v-if="currentSlide < storyBlocks.length - 1" :size="32" />
          <span v-else class="finish-btn">FINALIZAR</span>
        </button>
      </div>

      <!-- Abstract background decor -->
      <div class="bg-decor">
        <div class="blob b1"></div>
        <div class="blob b2"></div>
      </div>
    </div>
    
    <div v-else class="wrapped-error">
        <h2>SIN SEÑAL SUFICIENTE</h2>
        <p>Necesitas escuchar más música en Nebula para generar tu historia.</p>
        <button @click="router.push('/')" class="back-home-btn">VOLVER AL ESPACIO</button>
    </div>
  </div>
</template>

<style scoped>
.wrapped-experience {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 9999;
  background: #000;
  color: white;
  font-family: 'Outfit', sans-serif;
}

.wrapped-loading, .wrapped-error {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
}

.loader-content h2 { font-weight: 900; letter-spacing: 2px; margin-top: 20px; }
.loader-content p { color: rgba(255,255,255,0.5); }

.spinning { animation: rotate 2s linear infinite; color: #6366f1; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.story-container {
  height: 100%;
  width: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  transition: background 1s ease;
}

.progress-bar-container {
  position: absolute;
  top: 15px;
  left: 10px;
  right: 10px;
  display: flex;
  gap: 5px;
  z-index: 100;
}

.p-segment { flex: 1; height: 3px; background: rgba(255,255,255,0.15); border-radius: 2px; }
.p-fill {
  height: 100%; width: 0; background: white; border-radius: 2px; transition: width 0.3s;
}
.p-fill.active { width: 100%; opacity: 0.5; }
.p-fill.current { width: 100%; opacity: 1; box-shadow: 0 0 10px rgba(255,255,255,0.5); }

.close-btn {
  position: absolute;
  top: 30px;
  right: 20px;
  color: white;
  z-index: 100;
  opacity: 0.7;
}

.slide-content {
  text-align: center;
  z-index: 50;
  max-width: 90%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.slide-header { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.slide-meta { letter-spacing: 5px; font-weight: 800; font-size: 0.8rem; opacity: 0.7; text-transform: uppercase; }
.slide-text { font-size: 3.5rem; font-weight: 900; line-height: 1.1; letter-spacing: -2px; }

.slide-highlight {
  font-size: 5rem;
  font-weight: 1000;
  background: white;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 10px 20px rgba(0,0,0,0.3));
  margin-top: 20px;
}

.mini-sonar {
  width: 100px; height: 100px;
  border: 2px solid white;
  border-radius: 50%;
  animation: sonar 2s infinite;
  opacity: 0;
}
@keyframes sonar {
  0% { transform: scale(0.5); opacity: 1; }
  100% { transform: scale(3); opacity: 0; }
}

.touch-zones { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; z-index: 40; }
.zone { flex: 1; height: 100%; }

.controls {
  position: absolute;
  bottom: 40px;
  display: flex;
  gap: 60px;
  z-index: 100;
}

.finish-btn {
  background: white; color: black; padding: 10px 20px; border-radius: 30px; font-weight: 900; font-size: 0.8rem;
}

.bg-decor .blob {
  position: absolute;
  width: 600px; height: 600px;
  background: rgba(255,255,255,0.1);
  filter: blur(80px);
  border-radius: 50%;
}
.b1 { top: -200px; left: -200px; }
.b2 { bottom: -200px; right: -200px; }

.slide-fade-enter-active, .slide-fade-leave-active { transition: all 0.5s ease; }
.slide-fade-enter-from { opacity: 0; transform: translateX(50px); }
.slide-fade-leave-to { opacity: 0; transform: translateX(-50px); }

.back-home-btn {
  margin-top: 20px;
  background: #6366f1;
  color: white;
  padding: 12px 30px;
  border-radius: 30px;
  font-weight: 900;
}

@media (max-width: 768px) {
  .slide-text { font-size: 2.2rem; }
  .slide-highlight { font-size: 3rem; }
}
</style>
