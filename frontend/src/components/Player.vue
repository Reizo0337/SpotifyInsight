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
const progressTrackRef = ref<HTMLElement | null>(null)
const volTrackRef = ref<HTMLElement | null>(null)

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
  }
})

const tryPlay = async () => {
  if (!audioRef.value || !audioRef.value.src) return
  try {
    await audioRef.value.play()
    isPlaying.value = true
    musicStore.isPlaying = true
    musicStore.shouldAutoResume = false
  } catch (err) {
    console.warn('Playback blocked:', err)
    isPlaying.value = false
  }
}

watch(() => musicStore.isPlaying, (shouldPlay) => {
  if (shouldPlay && !isPlaying.value) {
    tryPlay()
  } else if (!shouldPlay && isPlaying.value) {
    audioRef.value?.pause()
    isPlaying.value = false
  }
})

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

watch(nowPlaying, (track) => {
  if (track) {
    musicStore.logTrackPlay(track)
  }
}, { immediate: true })

// Handlers
const togglePlay = () => {
  const a = audioRef.value
  if (!a || !a.src) return
  if (isPlaying.value) {
    a.pause()
    isPlaying.value = false
  } else {
    tryPlay()
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
  const a = audioRef.value
  if (!a) return

  if (!hasResumed.value) {
    const savedState = JSON.parse(localStorage.getItem('m-playback-state') || '{}')
    const currentId = musicStore.nowPlaying?.spotify_id || musicStore.nowPlaying?.id
    
    if (savedState.trackId === currentId) {
      const savedTime = Number(localStorage.getItem('m-time'))
      if (savedTime > 0 && savedTime < (a.duration || Infinity)) {
        a.currentTime = savedTime
      }
    } else {
      localStorage.setItem('m-time', '0')
    }
    hasResumed.value = true
  }

  if (musicStore.isPlaying || musicStore.shouldAutoResume) {
    tryPlay()
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
const handleInstantSeek = (e: MouseEvent) => {
  updateSeek(e)
  if (audioRef.value && duration.value) {
    audioRef.value.currentTime = (displayProgress.value / 100) * duration.value
  }
}

const startSeek = (e: MouseEvent) => {
  isDraggingProgress.value = true
  updateSeek(e)
  window.addEventListener('mousemove', updateSeek)
  window.addEventListener('mouseup', stopSeek)
}

const updateSeek = (e: MouseEvent) => {
  const bar = progressTrackRef.value
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
  const bar = volTrackRef.value
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
  <footer class="player-nebula">
    <audio 
      ref="audioRef" 
      @timeupdate="onTimeUpdate" 
      @ended="onEnded"
      @canplay="onCanPlay"
      @loadedmetadata="onTimeUpdate"
      crossorigin="anonymous"
    />

    <div class="player-container glass">
      <div class="glow-indicator" :class="{ 'active': isPlaying }"></div>
      
      <div class="track-zone">
        <div class="art-box" :class="{ 'playing': isPlaying, 'loading': streamLoading }">
          <img :src="nowPlaying?.thumbnail || `https://api.dicebear.com/7.x/shapes/svg?seed=${nowPlaying?.track_name}`" alt="">
          <div v-if="streamLoading" class="loader-overlay"><Loader2 :size="18" class="spin" /></div>
        </div>
        <div class="meta-box">
          <div class="title-scroller">
            <span class="track-name">{{ nowPlaying?.track_name || 'NEBULA CORE' }}</span>
          </div>
          <span class="artist-name">{{ nowPlaying?.artist || 'Ready for Signal' }}</span>
        </div>
      </div>

      <div class="commands-zone">
        <div class="button-row">
          <button class="icon-btn secondary" :class="{ active: isShuffle }" @click="musicStore.toggleShuffle" title="Shuffle"><Shuffle :size="16" /></button>
          <button class="icon-btn" @click="musicStore.playPrevious" title="Prev"><SkipBack :size="20" fill="currentColor" /></button>
          
          <button @click="togglePlay" class="play-trigger" :disabled="streamLoading && !streamUrl">
            <Loader2 v-if="streamLoading && !isPlaying" :size="24" class="spin" />
            <component v-else :is="isPlaying ? Pause : Play" :size="24" fill="white" />
          </button>

          <button class="icon-btn" @click="musicStore.playNext" title="Next"><SkipForward :size="20" fill="currentColor" /></button>
          <button class="icon-btn secondary" :class="{ active: loopMode !== 'off' }" @click="musicStore.toggleLoop" title="Loop">
            <Repeat :size="16" />
            <span v-if="loopMode === 'one'" class="one-badge">1</span>
          </button>
        </div>

        <div class="timeline-row">
          <span class="timestamp">{{ formatTime(currentTime) }}</span>
          <div class="progress-track" ref="progressTrackRef" @mousedown="startSeek" @click="handleInstantSeek">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: displayProgress + '%' }">
                  <div class="handle"></div>
              </div>
            </div>
          </div>
          <span class="timestamp">{{ formatTime(duration) }}</span>
        </div>
      </div>

      <div class="utilities-zone">
        <button class="speed-label" @click="cycleRate">{{ playbackRate }}x</button>
        <button class="icon-btn" @click="isQueueVisible = !isQueueVisible" :class="{ active: isQueueVisible }"><ListMusic :size="18" /></button>
        
        <div class="volume-control">
          <button class="icon-btn vol-icon" @click="toggleMute">
            <VolumeX v-if="isMuted || volume === 0" :size="18" />
            <Volume2 v-else :size="18" />
          </button>
          <div class="vol-track" ref="volTrackRef" @mousedown="startVol">
             <div class="vol-bar">
                <div class="vol-fill" :style="{ width: (isMuted ? 0 : volume * 100) + '%' }"></div>
             </div>
          </div>
        </div>
      </div>

      <!-- Live Stream Line Interface Decor -->
       <div class="stream-line">
           <div class="line-fill" :class="{ animate: isPlaying }"></div>
       </div>
    </div>

    <!-- Terminal Queue Interface -->
    <Transition name="queue-pop">
      <div v-if="isQueueVisible" class="queue-board glass">
        <div class="board-header">
          <div class="header-title">COLA DE PROCESAMIENTO</div>
          <button class="close-board" @click="isQueueVisible = false">×</button>
        </div>
        <div class="board-list custom-scrollbar">
          <div v-for="(t, i) in currentQueue" :key="i" 
               class="board-item" 
               :class="{ active: i === currentIndex }" 
               @click="musicStore._changeTrack(i)">
            <div class="item-id">{{ Number(i) + 1 }}</div>
            <div class="item-main">
                <span class="i-name">{{ t.track_name }}</span>
                <span class="i-artist">{{ t.artist }}</span>
            </div>
            <div v-if="i === currentIndex && isPlaying" class="pulse-icon"></div>
          </div>
        </div>
      </div>
    </Transition>
  </footer>
</template>

<style scoped>
.player-nebula {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 112px;
  padding: 0 16px 16px 16px;
  z-index: 9999;
  background: linear-gradient(to top, var(--nebula-bg) 80%, transparent);
}

.player-container {
  height: 96px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 30px 60px rgba(0,0,0,0.6);
}

.glow-indicator {
    position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--nebula-primary), transparent);
    opacity: 0;
    transition: opacity 0.5s;
}
.glow-indicator.active { opacity: 1; box-shadow: 0 0 15px var(--nebula-primary); }

.track-zone { display: flex; align-items: center; gap: 16px; width: 320px; }

.art-box {
    width: 60px; height: 60px;
    border-radius: 12px;
    position: relative;
    overflow: hidden;
    border: 1px solid var(--glass-border);
}
.art-box img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s; }
.playing .art-box img { transform: scale(1.1); }

.loader-overlay {
    position: absolute; inset: 0;
    background: rgba(0,0,0,0.5);
    display: flex; align-items: center; justify-content: center;
}

.meta-box { flex: 1; overflow: hidden; display: flex; flex-direction: column; gap: 2px; }
.track-name { font-size: 0.95rem; font-weight: 700; color: white; white-space: nowrap; }
.artist-name { font-size: 0.75rem; color: var(--nebula-text-dim); }

.commands-zone { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; }

.button-row { display: flex; align-items: center; gap: 24px; }

.play-trigger {
    width: 44px; height: 44px;
    background: var(--nebula-primary);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    box-shadow: 0 8px 16px rgba(99, 102, 241, 0.3);
}
.play-trigger:hover { transform: scale(1.1); box-shadow: 0 12px 24px rgba(99, 102, 241, 0.5); }
.play-trigger:disabled { opacity: 0.5; cursor: default; }

.icon-btn { color: var(--nebula-text-dim); transition: all 0.2s; }
.icon-btn:hover { color: white; transform: scale(1.1); }
.icon-btn.secondary { color: var(--nebula-text-muted); opacity: 0.6; }
.icon-btn.active { color: var(--nebula-primary); opacity: 1; filter: drop-shadow(0 0 5px var(--nebula-primary)); }

.timeline-row { width: 100%; max-width: 560px; display: flex; align-items: center; gap: 14px; }
.timestamp { font-size: 0.7rem; color: var(--nebula-text-muted); min-width: 35px; font-weight: 600; font-variant-numeric: tabular-nums; }

.progress-track { flex: 1; height: 20px; display: flex; align-items: center; cursor: pointer; }
.progress-bar { width: 100%; height: 4px; background: rgba(255,255,255,0.06); border-radius: 4px; position: relative; }
.progress-fill { height: 100%; background: var(--nebula-primary); border-radius: 4px; position: relative; }
.handle {
    position: absolute; right: -7px; top: 50%; transform: translateY(-50%);
    width: 14px; height: 14px; background: white; border-radius: 50%;
    opacity: 0; transition: opacity 0.2s;
    box-shadow: 0 0 10px var(--nebula-primary);
}
.progress-track:hover .handle { opacity: 1; }
.progress-track:hover .progress-bar { height: 6px; }

.utilities-zone { width: 320px; display: flex; align-items: center; justify-content: flex-end; gap: 16px; }

.speed-label {
    font-size: 0.65rem; font-weight: 800;
    color: var(--nebula-text-muted);
    background: rgba(255,255,255,0.05);
    padding: 3px 8px; border-radius: 6px;
    border: 1px solid var(--glass-border);
}

.volume-control { display: flex; align-items: center; gap: 10px; }
.vol-track { width: 90px; height: 16px; display: flex; align-items: center; cursor: pointer; }
.vol-bar { width: 100%; height: 3px; background: rgba(255,255,255,0.06); border-radius: 2px; }
.vol-fill { height: 100%; background: var(--nebula-text-muted); border-radius: 2px; }
.volume-control:hover .vol-fill { background: var(--nebula-accent); box-shadow: 0 0 8px var(--nebula-accent); }

.stream-line {
    position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: transparent; overflow: hidden;
}
.line-fill {
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, var(--nebula-accent), transparent);
    transform: translateX(-100%);
}
.line-fill.animate { animation: scan 3s linear infinite; }

@keyframes scan {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

.one-badge {
    position: absolute; top: 0; right: 0; font-size: 0.6rem; 
    font-weight: 900; background: var(--nebula-primary); color: white;
    width: 12px; height: 12px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
}

/* Queue Styles */
.queue-board {
    position: absolute; bottom: 110px; right: 16px;
    width: 320px; max-height: 440px;
    border-radius: 20px; padding: 20px;
    display: flex; flex-direction: column; gap: 16px;
    box-shadow: 0 30px 60px rgba(0,0,0,0.8);
}
.board-header { display: flex; align-items: center; justify-content: space-between; }
.header-title { font-size: 0.7rem; font-weight: 800; letter-spacing: 2px; color: var(--nebula-primary); }
.close-board { color: var(--nebula-text-muted); font-size: 1.2rem; }

.board-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; padding-right: 4px; }
.board-item {
    display: flex; align-items: center; gap: 12px; padding: 10px;
    border-radius: 12px; cursor: pointer; transition: all 0.2s;
    border: 1px solid transparent;
}
.board-item:hover { background: var(--nebula-surface-hover); border-color: var(--glass-border); }
.board-item.active { background: rgba(99, 102, 241, 0.1); border-color: rgba(99,102,241,0.3); }

.item-id { font-size: 0.7rem; font-weight: 800; color: var(--nebula-text-muted); width: 16px; }
.item-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.i-name { font-size: 0.85rem; font-weight: 600; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.i-artist { font-size: 0.7rem; color: var(--nebula-text-muted); }

.pulse-icon {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--nebula-accent);
    box-shadow: 0 0 10px var(--nebula-accent);
    animation: core-breath 1s ease-in-out infinite;
}

.queue-pop-enter-active, .queue-pop-leave-active { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.queue-pop-enter-from, .queue-pop-leave-to { opacity: 0; transform: translateY(20px) scale(0.9); }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 1024px) {
    .track-zone, .utilities-zone { width: 220px; }
    .timeline-row { max-width: 400px; }
}

@media (max-width: 768px) {
    .player-nebula { position: fixed; bottom: 0; left: 0; right: 0; padding: 12px; }
    .player-container { height: 80px; padding: 0 16px; border-radius: 16px; }
    .utilities-zone, .timeline-row, .icon-btn.secondary { display: none; }
    .track-zone { width: auto; flex: 1; }
    .commands-zone { flex: 0; }
    .button-row { gap: 16px; }
    .play-trigger { width: 40px; height: 40px; }
}
</style>
