<script setup lang="ts">
import { 
  Play, Pause, SkipBack, SkipForward, 
  Repeat, Shuffle, Volume2, VolumeX,
  ListMusic, MonitorSpeaker, Loader2
} from 'lucide-vue-next'
import { ref, watch, computed, onUnmounted } from 'vue'
import { useMusicStore } from '../stores/musicStore'

const musicStore = useMusicStore()
const audioRef = ref<HTMLAudioElement | null>(null)

const isPlaying = ref(false)
const progress = ref(0)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.7)
const isMuted = ref(false)
const playbackRate = ref(1)

const isDraggingProgress = ref(false)
const isDraggingVolume = ref(false)
const isQueueVisible = ref(false)

const streamLoading = computed(() => musicStore.isLoadingStream)
const streamUrl = computed(() => musicStore.streamUrl)
const streamMeta = computed(() => musicStore.streamMeta)
const nowPlaying = computed(() => musicStore.nowPlaying)
const loopMode = computed(() => musicStore.loopMode)
const isShuffle = computed(() => musicStore.isShuffle)
const currentQueue = computed(() => musicStore.currentQueue)
const currentIndex = computed(() => musicStore.currentIndex)

// Format seconds to m:ss
const formatTime = (secs: number) => {
  if (!secs || isNaN(secs)) return '0:00'
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

// Watch for stream URL changes — auto-play when ready
watch(streamUrl, (url) => {
  if (url && audioRef.value) {
    audioRef.value.src = url
    audioRef.value.volume = volume.value
    audioRef.value.playbackRate = playbackRate.value
    audioRef.value.play()
      .then(() => { isPlaying.value = true })
      .catch(err => console.error('Auto-play blocked:', err))
  }
})

// Watch for speed changes
watch(playbackRate, (rate) => {
  if (audioRef.value) {
    audioRef.value.playbackRate = rate
  }
})

// Watch for metadata changes to update duration
watch(streamMeta, (meta) => {
  if (meta?.duration) {
    duration.value = meta.duration
  }
})

const togglePlay = () => {
  const audio = audioRef.value
  if (!audio) return
  if (!audio.src && streamUrl.value) audio.src = streamUrl.value

  if (isPlaying.value) {
    audio.pause()
    isPlaying.value = false
  } else if (audio.src) {
    audio.play().then(() => { isPlaying.value = true }).catch(console.error)
  }
}

const onTimeUpdate = () => {
  const audio = audioRef.value
  if (!audio || isDraggingProgress.value) return
  currentTime.value = audio.currentTime
  // Use metadata duration as primary, fallback to element duration if ready
  if (audio.duration && !isNaN(audio.duration) && audio.duration !== Infinity) {
    duration.value = audio.duration
  }
  progress.value = duration.value ? (audio.currentTime / duration.value) * 100 : 0
}

const onEnded = () => {
  isPlaying.value = false
  if (loopMode.value === 'one' && audioRef.value) {
    audioRef.value.currentTime = 0
    audioRef.value.play()
    isPlaying.value = true
  } else {
    musicStore.playNext()
  }
}

// DRAGGING LOGIC
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
  progress.value = pct * 100
  currentTime.value = pct * duration.value
  if (!isDraggingProgress.value && audioRef.value) {
    audioRef.value.currentTime = currentTime.value
  }
}

const stopSeek = (e: MouseEvent) => {
  if (audioRef.value) {
    const bar = document.querySelector('.progress-container') as HTMLElement
    const rect = bar.getBoundingClientRect()
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
    audioRef.value.currentTime = pct * audioRef.value.duration
  }
  isDraggingProgress.value = false
  window.removeEventListener('mousemove', updateSeek)
  window.removeEventListener('mouseup', stopSeek)
}

const startVolumeDrag = (e: MouseEvent) => {
  isDraggingVolume.value = true
  updateVolume(e)
  window.addEventListener('mousemove', updateVolume)
  window.addEventListener('mouseup', stopVolumeDrag)
}

const updateVolume = (e: MouseEvent) => {
  const bar = document.querySelector('.volume-slider') as HTMLElement
  if (!bar) return
  const rect = bar.getBoundingClientRect()
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  volume.value = pct
  if (audioRef.value) audioRef.value.volume = pct
  isMuted.value = pct === 0
}

const stopVolumeDrag = () => {
  isDraggingVolume.value = false
  window.removeEventListener('mousemove', updateVolume)
  window.removeEventListener('mouseup', stopVolumeDrag)
}

const toggleMute = () => {
  isMuted.value = !isMuted.value
  if (audioRef.value) audioRef.value.muted = isMuted.value
}

const togglePlaybackRate = () => {
  const rates = [0.5, 0.75, 1, 1.25, 1.5, 2]
  const currentIndex = rates.indexOf(playbackRate.value)
  playbackRate.value = rates[(currentIndex + 1) % rates.length]
}

const toggleQueue = () => {
  isQueueVisible.value = !isQueueVisible.value
}

const playFromQueue = (index: number) => {
    musicStore.currentIndex = index
    const track = musicStore.currentQueue[index]
    musicStore.nowPlaying = track
    musicStore.streamTrack(track.track_name, track.artist || '')
}

onUnmounted(() => {
  audioRef.value?.pause()
  window.removeEventListener('mousemove', updateSeek)
  window.removeEventListener('mouseup', stopSeek)
  window.removeEventListener('mousemove', updateVolume)
  window.removeEventListener('mouseup', stopVolumeDrag)
})
</script>

<template>
  <footer class="player-2026">
    <!-- Hidden native audio element -->
    <audio 
      ref="audioRef" 
      @timeupdate="onTimeUpdate" 
      @ended="onEnded"
      @loadedmetadata="onTimeUpdate"
      crossorigin="anonymous"
    />

    <div class="player-wrapper">
      <!-- Top progress bar glow -->
      <div class="mini-progress-top">
        <div class="mini-fill" :style="{ width: progress + '%' }"></div>
      </div>

      <!-- Track Info -->
      <div class="track-info">
        <div class="album-art" :class="{ 'playing': isPlaying, 'loading': streamLoading }">
          <img 
            :src="nowPlaying?.thumbnail || `https://api.dicebear.com/7.x/identicon/svg?seed=${nowPlaying?.track_name || 'music'}`" 
            alt="Art"
          >
          <div class="art-glow"></div>
          <div v-if="streamLoading" class="art-loading">
            <Loader2 :size="20" class="spin" />
          </div>
        </div>
        <div class="track-details">
          <span class="title">{{ nowPlaying?.track_name || 'Selecciona una canción' }}</span>
          <span class="artist">{{ nowPlaying?.artist || 'Insights Engine' }}</span>
        </div>
      </div>

      <!-- Center Controls -->
      <div class="controls-section">
        <div class="main-buttons">
          <button class="btn-icon secondary" :class="{ active: isShuffle }" @click="musicStore.toggleShuffle">
            <Shuffle :size="18" />
          </button>
          <button class="btn-icon secondary" @click="musicStore.playPrevious">
            <SkipBack :size="20" fill="currentColor" />
          </button>
          <button @click="togglePlay" class="play-btn" :disabled="streamLoading && !streamUrl">
            <Loader2 v-if="streamLoading && !isPlaying" :size="22" class="spin" />
            <component v-else :is="isPlaying ? Pause : Play" :size="22" fill="black" />
          </button>
          <button class="btn-icon secondary" @click="musicStore.playNext">
            <SkipForward :size="20" fill="currentColor" />
          </button>
          <button class="btn-icon secondary" :class="{ active: loopMode !== 'off' }" @click="musicStore.toggleLoop" style="position: relative;">
            <Repeat :size="18" />
            <span v-if="loopMode === 'one'" class="loop-one-indicator">1</span>
          </button>
        </div>

        <!-- Playback Bar -->
        <div class="playback-bar">
          <span class="time">{{ formatTime(currentTime) }}</span>
          <div class="progress-container" @mousedown="startSeek">
            <div class="progress-bg">
              <div class="progress-fill" :style="{ width: progress + '%' }">
                <div class="progress-knob"></div>
              </div>
            </div>
          </div>
          <span class="time">{{ formatTime(duration - currentTime) }}</span>
        </div>
      </div>

      <!-- Extra Controls -->
      <div class="extra-controls">
        <button class="btn-icon speed-btn" @click="togglePlaybackRate" title="Velocidad">
          {{ playbackRate }}x
        </button>
        <button class="btn-icon" @click="toggleQueue" :class="{ active: isQueueVisible }">
          <ListMusic :size="18" />
        </button>
        <button class="btn-icon"><MonitorSpeaker :size="18" /></button>
        <div class="volume-group">
          <button class="btn-icon" @click="toggleMute">
            <VolumeX v-if="isMuted || volume === 0" :size="18" />
            <Volume2 v-else :size="18" />
          </button>
          <div class="volume-slider" @mousedown="startVolumeDrag">
            <div class="volume-fill" :style="{ width: (isMuted ? 0 : volume * 100) + '%' }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Queue Overlay -->
    <Transition name="slide-up">
      <div v-if="isQueueVisible" class="queue-overlay">
        <div class="queue-header">
          <h3>Cola de Reproducción</h3>
          <button class="close-btn" @click="toggleQueue">×</button>
        </div>
        <div class="queue-list custom-scrollbar">
          <div 
            v-for="(track, index) in currentQueue" 
            :key="track.spotify_id + index"
            class="queue-item"
            :class="{ 'current': index === currentIndex }"
            @click="playFromQueue(index)"
          >
            <div class="q-thumb">
              <img :src="track.thumbnail || `https://api.dicebear.com/7.x/shapes/svg?seed=${track.track_name}`" alt="">
              <div v-if="index === currentIndex" class="playing-overlay">
                <Loader2 v-if="isPlaying" :size="14" class="spin" />
              </div>
            </div>
            <div class="q-info">
              <span class="q-name">{{ track.track_name }}</span>
              <span class="q-artist">{{ track.artist }}</span>
            </div>
            <div class="q-actions">
                <button class="q-remove" @click.stop="musicStore.removeFromQueue(index)">×</button>
            </div>
          </div>
          <div v-if="currentQueue.length === 0" class="empty-queue">
            No hay canciones en la cola
          </div>
        </div>
      </div>
    </Transition>
  </footer>
</template>

<style scoped>
.player-2026 {
  grid-area: player;
  padding: 8px 0 16px 0;
  z-index: 100;
}

.player-wrapper {
  background: rgba(15, 15, 15, 0.6);
  backdrop-filter: blur(40px) saturate(200%);
  -webkit-backdrop-filter: blur(40px) saturate(200%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin: 0 16px;
  border-radius: 24px;
  height: 96px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  box-shadow: 0 30px 60px rgba(0,0,0,0.6);
  position: relative;
  overflow: hidden;
}

.mini-progress-top {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: rgba(255,255,255,0.05);
}

.mini-fill {
  height: 100%;
  background: var(--spotify-neon);
  box-shadow: 0 0 15px var(--spotify-neon);
  transition: width 0.3s linear;
  border-radius: 2px;
}

.track-info {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 30%;
}

.album-art {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  position: relative;
  transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  flex-shrink: 0;
}

.album-art.playing {
  transform: scale(1.05);
}

.album-art img {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  object-fit: cover;
  position: relative;
  z-index: 2;
}

.art-glow {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 100%; height: 100%;
  background: var(--spotify-green);
  filter: blur(20px);
  opacity: 0;
  transition: opacity 0.5s;
  z-index: 1;
}

.playing .art-glow {
  opacity: 0.4;
}

.art-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.5);
  border-radius: 12px;
  z-index: 3;
  color: white;
}

.track-details {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.title {
  font-size: 0.95rem;
  font-weight: 700;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.artist {
  font-size: 0.8rem;
  color: var(--spotify-text-grey);
}

.controls-section {
  flex: 1;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.main-buttons {
  display: flex;
  align-items: center;
  gap: 24px;
}

.play-btn {
  width: 42px;
  height: 42px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: black;
  transition: all 0.2s;
}

.play-btn:hover:not(:disabled) {
  transform: scale(1.1);
  background: var(--spotify-neon);
}

.play-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  color: var(--spotify-text-grey);
  padding: 4px;
  transition: all 0.2s;
}

.btn-icon:hover { color: white; }

.btn-icon.secondary { opacity: 0.7; }
.btn-icon.active { color: var(--spotify-green); opacity: 1; }

.playback-bar {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
}

.time {
  font-size: 0.72rem;
  color: var(--spotify-text-grey);
  min-width: 35px;
  font-variant-numeric: tabular-nums;
}

.progress-container {
  flex: 1;
  height: 16px;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.progress-bg {
  width: 100%;
  height: 4px;
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: white;
  border-radius: 2px;
  position: relative;
  transition: width 0.1s linear, background 0.2s;
}

.progress-container:hover .progress-fill {
  background: var(--spotify-green);
}

.progress-knob {
  position: absolute;
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.1s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.4);
}

.progress-container:hover .progress-knob {
  opacity: 1;
}

.extra-controls {
  width: 30%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.volume-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.volume-slider {
  width: 90px;
  height: 16px;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.volume-slider::before {
  content: '';
  position: absolute;
  width: 90px;
  height: 4px;
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
}

.volume-fill {
  height: 4px;
  background: white;
  border-radius: 2px;
  position: relative;
  transition: width 0.1s;
  min-width: 2px;
}

.volume-group:hover .volume-fill {
  background: var(--spotify-green);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loop-one-indicator {
  position: absolute;
  top: 0;
  right: -4px;
  background: var(--spotify-green);
  color: black;
  font-size: 0.6rem;
  font-weight: 900;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 5px var(--spotify-green);
}

.speed-btn {
  font-size: 0.7rem;
  font-weight: 800;
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
  padding: 2px 6px;
  min-width: 34px;
}

/* ─── Queue Overlay ─────────────────────────────── */
.queue-overlay {
  position: absolute;
  bottom: 110px;
  right: 16px;
  width: 320px;
  max-height: 400px;
  background: rgba(20, 20, 20, 0.85);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.8);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 1000;
}

.queue-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.queue-header h3 {
  margin: 0;
  font-size: 0.95rem;
  background: var(--spotify-green-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.close-btn {
  font-size: 1.5rem;
  color: var(--spotify-text-grey);
}

.queue-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.queue-item:hover {
  background: rgba(255,255,255,0.05);
}

.queue-item.current {
  background: rgba(29, 185, 84, 0.1);
}

.q-thumb {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.q-thumb img { width: 100%; height: 100%; object-fit: cover; }

.playing-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-neon);
}

.q-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.q-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.q-artist {
  font-size: 0.75rem;
  color: var(--spotify-text-grey);
}

.q-remove {
  color: var(--spotify-text-grey);
  font-size: 1.2rem;
  padding: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.queue-item:hover .q-remove { opacity: 1; }
.q-remove:hover { color: #ff5555; }

.empty-queue {
  padding: 32px;
  text-align: center;
  color: var(--spotify-text-grey);
  font-size: 0.8rem;
}

/* ─── Transitions ────────────────────────────────── */
.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from, .slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

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
