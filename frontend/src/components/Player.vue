<script setup lang="ts">
import { 
  Play, Pause, SkipBack, SkipForward, 
  Repeat, Shuffle, Volume2, VolumeX,
  ListMusic, MonitorSpeaker, Loader2
} from 'lucide-vue-next'
import { ref, watch, computed, onUnmounted, onMounted } from 'vue'
import { useMusicStore } from '../stores/musicStore'

const musicStore = useMusicStore()
const audioRef = ref<HTMLAudioElement | null>(null)

// UI State
const isPlaying = ref(false)
const displayProgress = ref(0) // Local state for smooth dragging
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(musicStore.volume)
const isMuted = ref(false)
const playbackRate = ref(musicStore.playbackRate)
const hasResumed = ref(false)
const isDraggingProgress = ref(false)
const isDraggingVolume = ref(false)
const isQueueVisible = ref(false)

// Store Mappings
const streamLoading = computed(() => musicStore.isLoadingStream)
const streamUrl = computed(() => musicStore.streamUrl)
const streamMeta = computed(() => musicStore.streamMeta)
const nowPlaying = computed(() => musicStore.activeTrack)
const loopMode = computed(() => musicStore.loopMode)
const isShuffle = computed(() => musicStore.isShuffle)
const currentQueue = computed(() => musicStore.currentQueue)
const currentIndex = computed(() => musicStore.currentIndex)

const formatTime = (secs: number) => {
  if (!secs || isNaN(secs)) return '0:00'
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

// Watchers
watch(streamUrl, (url) => {
  if (url && audioRef.value) {
    audioRef.value.src = url
    audioRef.value.volume = isMuted.value ? 0 : volume.value
    audioRef.value.playbackRate = playbackRate.value
    hasResumed.value = false
    
    // Regular play (not reload)
    if (!musicStore.shouldAutoResume) {
      audioRef.value.play().then(() => { isPlaying.value = true }).catch(() => {})
    }
  }
})

// Trigger auto-resume from reload
watch(() => musicStore.shouldAutoResume, (val) => {
  if (val && audioRef.value && audioRef.value.src) {
    audioRef.value.play()
      .then(() => { 
        isPlaying.value = true
        musicStore.shouldAutoResume = false 
      })
      .catch(err => {
        console.warn('Auto-play blocked by browser. User interaction required.', err)
        musicStore.shouldAutoResume = false
      })
  }
}, { immediate: true })

watch(isPlaying, (val) => {
  musicStore.savePlaybackState(val)
})

watch(playbackRate, (rate) => {
  if (audioRef.value) audioRef.value.playbackRate = rate
  musicStore.updatePlaybackRate(rate)
})

watch(streamMeta, (meta) => {
  if (meta?.duration) duration.value = meta.duration
})

// Handlers
const togglePlay = () => {
  const a = audioRef.value
  if (!a || !a.src) return
  if (isPlaying.value) {
    a.pause()
    isPlaying.value = false
  } else {
    a.play().then(() => { isPlaying.value = true }).catch(console.error)
  }
}

const onTimeUpdate = () => {
  const a = audioRef.value
  if (!a || isDraggingProgress.value) return
  
  currentTime.value = a.currentTime
  if (a.duration && !isNaN(a.duration) && a.duration !== Infinity) {
    duration.value = a.duration
  }
  displayProgress.value = duration.value ? (a.currentTime / duration.value) * 100 : 0
  
  if (isPlaying.value) musicStore.updatePersistedTime(a.currentTime)
}

const onCanPlay = () => {
  if (!hasResumed.value && audioRef.value) {
    const saved = Number(localStorage.getItem('m-time'))
    if (saved > 0 && saved < (audioRef.value.duration || Infinity)) {
      audioRef.value.currentTime = saved
    }
    hasResumed.value = true
  }
}

const onEnded = () => {
  if (loopMode.value === 'one' && audioRef.value) {
    audioRef.value.currentTime = 0
    audioRef.value.play()
  } else {
    musicStore.playNext()
  }
}

// Interaction logic
const startSeek = (e: MouseEvent) => {
  isDraggingProgress.value = true
  updateSeek(e)
  window.addEventListener('mousemove', updateSeek)
  window.addEventListener('mouseup', stopSeek)
}

const updateSeek = (e: MouseEvent) => {
  const bar = document.querySelector('.progress-container') as HTMLElement
  if (!bar || !duration.value) return
  const rect = bar.getBoundingClientRect()
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  displayProgress.value = pct * 100
  currentTime.value = pct * duration.value
}

const stopSeek = () => {
  if (audioRef.value && duration.value) {
    audioRef.value.currentTime = (displayProgress.value / 100) * duration.value
  }
  isDraggingProgress.value = false
  window.removeEventListener('mousemove', updateSeek)
  window.removeEventListener('mouseup', stopSeek)
}

const startVol = (e: MouseEvent) => {
  isDraggingVolume.value = true
  updateVol(e)
  window.addEventListener('mousemove', updateVol)
  window.addEventListener('mouseup', stopVol)
}

const updateVol = (e: MouseEvent) => {
  const bar = document.querySelector('.volume-slider') as HTMLElement
  if (!bar) return
  const rect = bar.getBoundingClientRect()
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  volume.value = pct
  if (audioRef.value) audioRef.value.volume = pct
  musicStore.updateVolume(pct)
}

const stopVol = () => {
  isDraggingVolume.value = false
  window.removeEventListener('mousemove', updateVol)
  window.removeEventListener('mouseup', stopVol)
}

const toggleMute = () => {
  isMuted.value = !isMuted.value
  if (audioRef.value) audioRef.value.muted = isMuted.value
}

const cycleRate = () => {
  const rates = [0.5, 1, 1.25, 1.5, 2]
  playbackRate.value = rates[(rates.indexOf(playbackRate.value) + 1) % rates.length]
}

const onUnload = () => {
  musicStore.savePlaybackState(isPlaying.value)
}

onMounted(() => {
  if (musicStore.nowPlaying) musicStore.loadPlaybackState()
  window.addEventListener('beforeunload', onUnload)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', updateSeek)
  window.removeEventListener('mouseup', stopSeek)
  window.removeEventListener('mousemove', updateVol)
  window.removeEventListener('mouseup', stopVol)
  window.removeEventListener('beforeunload', onUnload)
})

</script>

<template>
  <footer class="player-2026">
    <audio 
      ref="audioRef" 
      @timeupdate="onTimeUpdate" 
      @ended="onEnded"
      @canplay="onCanPlay"
      @loadedmetadata="onTimeUpdate"
      crossorigin="anonymous"
    />

    <div class="player-wrapper">
      <div class="mini-progress-top">
        <div class="mini-fill" :style="{ width: displayProgress + '%' }"></div>
      </div>

      <div class="track-info">
        <div class="album-art" :class="{ 'playing': isPlaying, 'loading': streamLoading }">
          <img :src="nowPlaying?.thumbnail || `https://api.dicebear.com/7.x/identicon/svg?seed=${nowPlaying?.track_name}`" alt="">
          <div class="art-glow"></div>
          <div v-if="streamLoading" class="art-loading"><Loader2 :size="20" class="spin" /></div>
        </div>
        <div class="track-details">
          <span class="title">{{ nowPlaying?.track_name || 'Sin reproducción' }}</span>
          <span class="artist">{{ nowPlaying?.artist || 'Inicia una canción' }}</span>
        </div>
      </div>

      <div class="controls-section">
        <div class="main-buttons">
          <button class="btn-icon secondary" :class="{ active: isShuffle }" @click="musicStore.toggleShuffle"><Shuffle :size="18" /></button>
          <button class="btn-icon secondary" @click="musicStore.playPrevious"><SkipBack :size="20" fill="currentColor" /></button>
          <button @click="togglePlay" class="play-btn" :disabled="streamLoading && !streamUrl">
            <Loader2 v-if="streamLoading && !isPlaying" :size="22" class="spin" />
            <component v-else :is="isPlaying ? Pause : Play" :size="22" fill="black" />
          </button>
          <button class="btn-icon secondary" @click="musicStore.playNext"><SkipForward :size="20" fill="currentColor" /></button>
          <button class="btn-icon secondary" :class="{ active: loopMode !== 'off' }" @click="musicStore.toggleLoop">
            <Repeat :size="18" />
            <span v-if="loopMode === 'one'" class="loop-one-indicator">1</span>
          </button>
        </div>

        <div class="playback-bar">
          <span class="time">{{ formatTime(currentTime) }}</span>
          <div class="progress-container" @mousedown="startSeek">
            <div class="progress-bg">
              <div class="progress-fill" :style="{ width: displayProgress + '%' }"><div class="progress-knob"></div></div>
            </div>
          </div>
          <span class="time">{{ formatTime(duration) }}</span>
        </div>
      </div>

      <div class="extra-controls">
        <button class="btn-icon speed-btn" @click="cycleRate">{{ playbackRate }}x</button>
        <button class="btn-icon" @click="isQueueVisible = !isQueueVisible" :class="{ active: isQueueVisible }"><ListMusic :size="18" /></button>
        <button class="btn-icon"><MonitorSpeaker :size="18" /></button>
        <div class="volume-group">
          <button class="btn-icon" @click="toggleMute">
            <VolumeX v-if="isMuted || volume === 0" :size="18" />
            <Volume2 v-else :size="18" />
          </button>
          <div class="volume-slider" @mousedown="startVol">
            <div class="volume-fill" :style="{ width: (isMuted ? 0 : volume * 100) + '%' }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Queue Overlay -->
    <Transition name="slide-up">
      <div v-if="isQueueVisible" class="queue-overlay">
        <div class="queue-header">
          <h3>Siguiente en la cola</h3>
          <button @click="isQueueVisible = false">×</button>
        </div>
        <div class="queue-list custom-scrollbar">
          <div v-for="(t, i) in currentQueue" :key="i" class="queue-item" :class="{ current: i === currentIndex }" @click="musicStore._changeTrack(i)">
            <div class="q-thumb">
              <img :src="t.thumbnail || `https://api.dicebear.com/7.x/shapes/svg?seed=${t.track_name}`" alt="">
              <div v-if="i === currentIndex && isPlaying" class="playing-overlay"><Loader2 :size="14" class="spin" /></div>
            </div>
            <div class="q-info">
              <span class="q-name">{{ t.track_name }}</span>
              <span class="q-artist">{{ t.artist }}</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </footer>
</template>

<style scoped>
.player-2026 { grid-area: player; padding-bottom: 16px; position: relative; }
.player-wrapper {
  background: rgba(18, 18, 18, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin: 0 16px;
  border-radius: 20px;
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.5);
  position: relative;
  overflow: hidden;
}
.mini-progress-top { position: absolute; top: 0; left: 0; right: 0; height: 2px; background: rgba(255,255,255,0.05); }
.mini-fill { height: 100%; background: var(--spotify-neon); transition: width 0.2s linear; }
.track-info { display: flex; align-items: center; gap: 12px; width: 300px; }
.album-art { width: 52px; height: 52px; border-radius: 8px; position: relative; flex-shrink: 0; }
.album-art img { width: 100%; height: 100%; border-radius: 8px; object-fit: cover; }
.art-glow { position: absolute; inset: 0; background: var(--spotify-green); filter: blur(15px); opacity: 0; transition: opacity 0.4s; }
.playing .art-glow { opacity: 0.3; }
.art-loading { position: absolute; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; border-radius: 8px; }
.track-details { display: flex; flex-direction: column; overflow: hidden; }
.title { font-size: 0.9rem; font-weight: 700; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.artist { font-size: 0.75rem; color: var(--spotify-text-grey); }
.controls-section { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.main-buttons { display: flex; align-items: center; gap: 20px; }
.play-btn { width: 38px; height: 38px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: black; transition: transform 0.2s; }
.play-btn:hover { transform: scale(1.08); }
.btn-icon { color: var(--spotify-text-grey); padding: 4px; transition: color 0.2s; }
.btn-icon:hover { color: white; }
.btn-icon.active { color: var(--spotify-green); }
.playback-bar { width: 100%; max-width: 500px; display: flex; align-items: center; gap: 12px; }
.time { font-size: 0.7rem; color: var(--spotify-text-grey); min-width: 35px; font-variant-numeric: tabular-nums; }
.progress-container { flex: 1; height: 12px; display: flex; align-items: center; cursor: pointer; }
.progress-bg { width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; position: relative; }
.progress-fill { height: 100%; background: white; border-radius: 2px; position: relative; }
.progress-knob { position: absolute; right: -6px; top: 50%; transform: translateY(-50%); width: 12px; height: 12px; background: white; border-radius: 50%; opacity: 0; transition: opacity 0.1s; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.progress-container:hover .progress-knob { opacity: 1; }
.progress-container:hover .progress-fill { background: var(--spotify-green); }
.extra-controls { width: 300px; display: flex; align-items: center; justify-content: flex-end; gap: 12px; }
.volume-group { display: flex; align-items: center; gap: 8px; }
.volume-slider { width: 80px; height: 12px; position: relative; display: flex; align-items: center; cursor: pointer; }
.volume-slider::before { content: ''; position: absolute; width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; }
.volume-fill { height: 4px; background: white; border-radius: 2px; min-width: 4px; }
.volume-group:hover .volume-fill { background: var(--spotify-green); }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.loop-one-indicator { position: absolute; top: -2px; right: -4px; background: var(--spotify-green); color: black; font-size: 0.6rem; font-weight: 900; width: 12px; height: 12px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.speed-btn { font-size: 0.7rem; font-weight: 800; background: rgba(255,255,255,0.05); border-radius: 4px; padding: 2px 6px; }

/* ─── Queue Variables ──────────────────────────────── */

.queue-overlay { position: absolute; bottom: 100px; right: 16px; width: 300px; max-height: 400px; background: rgba(24, 24, 24, 0.9); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); display: flex; flex-direction: column; overflow: hidden; }
.queue-header { padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05); }
.queue-header h3 { margin: 0; font-size: 0.85rem; color: var(--primary-blue); text-transform: uppercase; letter-spacing: 0.05em; }
.queue-list { flex: 1; overflow-y: auto; padding: 8px; }
.queue-item { display: flex; align-items: center; gap: 10px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s; }
.queue-item:hover { background: rgba(33, 101, 255, 0.15); }
.queue-item.current { background: rgba(33, 101, 255, 0.25); border: 1px solid rgba(33, 101, 255, 0.3); }
.q-thumb { width: 32px; height: 32px; border-radius: 4px; position: relative; overflow: hidden; }
.q-thumb img { width: 100%; height: 100%; object-fit: cover; }
.playing-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; color: var(--primary-blue); }
.q-info { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.q-name { font-size: 0.8rem; font-weight: 600; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.q-artist { font-size: 0.7rem; color: var(--spotify-text-grey); }
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(10px); }

/* ─── Mobile ─────────────────────────────────────── */
@media (max-width: 768px) {
  .player-2026 {
    position: fixed;
    bottom: 64px;
    left: 0;
    right: 0;
    padding: 8px 12px;
    background: transparent;
  }

  .player-wrapper {
    margin: 0;
    border-radius: 16px;
    height: 76px;
    padding: 0 16px;
    background: rgba(20, 20, 20, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(21,101,255,0.1);
  }

  .extra-controls, .playback-bar, .btn-icon.secondary {
    display: none;
  }

  .track-info {
    width: auto;
    flex: 1;
  }

  .album-art {
    width: 48px;
    height: 48px;
  }

  .title { font-size: 0.85rem; }
  .artist { font-size: 0.72rem; }

  .controls-section {
    width: auto;
    flex-direction: row;
    max-width: none;
    gap: 0;
    justify-content: flex-end;
  }

  .main-buttons {
    gap: 12px;
  }

  .play-btn {
    width: 38px;
    height: 38px;
  }

  .queue-overlay {
      width: calc(100% - 32px);
      bottom: 90px;
      right: 16px;
  }
}
</style>
