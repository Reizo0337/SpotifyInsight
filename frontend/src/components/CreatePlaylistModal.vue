<script setup lang="ts">
import { ref, watch } from 'vue'
import { X, Music, Download, Link, Search, AlertTriangle } from 'lucide-vue-next'
import { useMusicStore } from '../stores/musicStore'

const musicStore = useMusicStore()
const playlistName = ref('')
const spotifyUrl = ref('')
const activeTab = ref<'manual' | 'spotify'>('manual')
const inputRef = ref<HTMLInputElement | null>(null)
const isLoadingInfo = ref(false)
const playlistPreview = ref<any>(null)
const selectedTargetId = ref<string>('')

// Import state
const importPhase = ref<1 | 2>(1)
const importState = ref<'idle' | 'confirm' | 'importing' | 'done' | 'error'>('idle')
const importProgress = ref(0)
const importTotal = ref(0)
const importCurrentTrack = ref('')
const importMessage = ref('')
const importDoneCount = ref(0)
const importPhaseLabel = ref('')

const closeModal = () => {
  if (importState.value === 'importing') return // block close while importing
  musicStore.isCreateModalOpen = false
  playlistName.value = ''
  spotifyUrl.value = ''
  playlistPreview.value = null
  selectedTargetId.value = ''
  activeTab.value = 'manual'
  importPhase.value = 1
  importState.value = 'idle'
  importProgress.value = 0
  importTotal.value = 0
  importCurrentTrack.value = ''
  importMessage.value = ''
  importPhaseLabel.value = ''
}

const handleCreate = async () => {
  if (playlistName.value.trim()) {
    await musicStore.createPlaylist(playlistName.value.trim())
    closeModal()
  }
}

const loadPlaylistInfo = async () => {
  if (!spotifyUrl.value) return
  isLoadingInfo.value = true
  try {
    const info = await musicStore.fetchSpotifyPlaylistInfo(spotifyUrl.value)
    if (info) {
      playlistPreview.value = info
      importState.value = 'idle'
    }
  } finally {
    isLoadingInfo.value = false
  }
}

const confirmImport = () => {
  importState.value = 'confirm'
}

const cancelImport = () => {
  importState.value = 'idle'
}

const handleImport = async () => {
  if (!playlistPreview.value) return
  importState.value = 'importing'
  importPhase.value = 1
  importProgress.value = 0
  importTotal.value = 0
  importCurrentTrack.value = ''
  importMessage.value = 'Iniciando importación...'
  importPhaseLabel.value = ''

  const pid = playlistPreview.value.id
  const name = encodeURIComponent(playlistPreview.value.name)
  const targetId = encodeURIComponent(selectedTargetId.value || '')
  const url = `http://localhost:8000/api/spotify/playlists/import/stream?playlist_id=${pid}&name=${name}&target_playlist_id=${targetId}`

  const evtSource = new EventSource(url)

  evtSource.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    switch (msg.type) {
      case 'playlist_created':
        importMessage.value = `Playlist "${msg.name}" creada`
        break
      case 'status':
        importMessage.value = msg.message
        break
      case 'total':
        importTotal.value = msg.count
        importMessage.value = `Encontradas ${msg.count} canciones — obteniendo metadatos...`
        break
      case 'analyzing':
        importCurrentTrack.value = `${msg.artist} - ${msg.track}`
        if (importTotal.value > 0) {
          importProgress.value = Math.round(((msg.current - 1) / importTotal.value) * 100)
        }
        break
      case 'phase2_start':
        importPhase.value = 2
        importProgress.value = 0
        importMessage.value = msg.message
        importPhaseLabel.value = 'Buscando en YouTube...'
        break
      case 'progress':
        if (importTotal.value > 0) {
          importProgress.value = Math.round((msg.current / importTotal.value) * 100)
        }
        importPhaseLabel.value = msg.phase_label || ''
        break
      case 'done':
        importDoneCount.value = msg.track_count
        importProgress.value = 100
        importState.value = 'done'
        evtSource.close()
        musicStore.fetchPlaylists()
        break
      case 'error':
        importMessage.value = msg.message
        importState.value = 'error'
        evtSource.close()
        break
    }
  }

  evtSource.onerror = () => {
    if (importState.value !== 'done') {
      importMessage.value = 'Error de conexión con el servidor'
      importState.value = 'error'
    }
    evtSource.close()
  }
}

watch(() => musicStore.isCreateModalOpen, (isOpen) => {
  if (isOpen) {
    if (activeTab.value === 'manual') {
      setTimeout(() => inputRef.value?.focus(), 50)
    }
  }
})
</script>

<template>
  <Transition name="modal-fade">
    <div v-if="musicStore.isCreateModalOpen" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <div class="tabs">
            <button :class="{ active: activeTab === 'manual' }" @click="activeTab = 'manual'" :disabled="importState === 'importing'">Crear Manual</button>
            <button :class="{ active: activeTab === 'spotify' }" @click="activeTab = 'spotify'" :disabled="importState === 'importing'">Importar por Enlace</button>
          </div>
          <button class="close-btn" @click="closeModal" :disabled="importState === 'importing'"><X :size="20" /></button>
        </div>
        
        <div class="modal-body">
          <Transition name="fade" mode="out-in">
            <!-- Manual Create -->
            <div v-if="activeTab === 'manual'" key="manual" class="tab-content">
              <div class="input-group">
                <label for="pl-name">Nombre de la playlist</label>
                <input 
                  id="pl-name"
                  ref="inputRef"
                  v-model="playlistName" 
                  type="text" 
                  placeholder="Mi playlist n.º 1"
                  @keyup.enter="handleCreate"
                />
              </div>
              <p class="disclaimer">Al crear una playlist, podrás añadir canciones desde cualquier menú de opciones.</p>
              
              <div class="modal-footer">
                <button class="cancel-btn" @click="closeModal">Cancelar</button>
                <button 
                  class="confirm-btn" 
                  :disabled="!playlistName.trim()" 
                  @click="handleCreate"
                >
                  Crear
                </button>
              </div>
            </div>

            <!-- Spotify Import by URL -->
            <div v-else key="spotify" class="tab-content spotify-import-url">

              <!-- IMPORTING STATE -->
              <div v-if="importState === 'importing' || importState === 'done' || importState === 'error'" class="import-progress-view">
                <div v-if="importState === 'done'" class="done-header">
                  <div class="done-icon">✓</div>
                  <h3>¡Importación completa!</h3>
                  <p>{{ importDoneCount }} canciones añadidas y analizadas</p>
                </div>
                <div v-else-if="importState === 'error'" class="error-header">
                  <AlertTriangle :size="40" class="error-icon" />
                  <h3>Error en la importación</h3>
                  <p>{{ importMessage }}</p>
                </div>
                <div v-else class="importing-header">
                  <div class="spinner-ring"></div>
                  <h3>{{ importPhase === 1 ? 'Preparando canciones...' : 'Obteniendo links de audio...' }}</h3>
                  <p class="current-track-label">
                    {{ importPhaseLabel || importCurrentTrack || importMessage }}
                  </p>
                  <div class="phase-badge" :class="{ 'phase-2': importPhase === 2 }">
                    Fase {{ importPhase }}/2: {{ importPhase === 1 ? 'Metadatos' : 'YouTube (×6)' }}
                  </div>
                </div>

                <div class="progress-bar-wrap" v-if="importTotal > 0">
                  <div class="progress-bar-track">
                    <div class="progress-bar-fill" :style="{ width: importProgress + '%' }"></div>
                  </div>
                  <div class="progress-numbers">
                    <span>{{ importProgress }}%</span>
                    <span v-if="importState === 'importing'">{{ Math.round(importProgress / 100 * importTotal) }} / {{ importTotal }} canciones</span>
                  </div>
                </div>

                <div class="modal-footer" v-if="importState === 'done' || importState === 'error'">
                  <button class="confirm-btn" @click="closeModal">Cerrar</button>
                </div>
              </div>

              <!-- CONFIRM STATE -->
              <div v-else-if="importState === 'confirm'" class="confirm-view">
                <div class="confirm-icon"><AlertTriangle :size="44" /></div>
                <h3>¿Importar esta playlist?</h3>
                <p class="confirm-desc">
                  Se descargarán los datos de <strong>{{ playlistPreview?.track_count }} canciones</strong> y se buscará un enlace de audio para cada una.<br><br>
                  <strong>Esto puede tardar varios minutos.</strong>
                </p>
                <div class="modal-footer">
                  <button class="cancel-btn" @click="cancelImport">Cancelar</button>
                  <button class="confirm-btn" @click="handleImport">Sí, importar</button>
                </div>
              </div>

              <!-- NORMAL STATE -->
              <div v-else>
                <div class="input-group">
                  <label for="sp-url">Enlace de la playlist de Spotify</label>
                  <div class="search-input-wrapper">
                    <input 
                      id="sp-url"
                      v-model="spotifyUrl" 
                      type="text" 
                      placeholder="https://open.spotify.com/playlist/..."
                      @keyup.enter="loadPlaylistInfo"
                    />
                    <button class="search-btn" @click="loadPlaylistInfo" :disabled="isLoadingInfo">
                      <Search v-if="!isLoadingInfo" :size="18" />
                      <span v-else class="loader-small"></span>
                    </button>
                  </div>
                </div>

                <div v-if="playlistPreview" class="preview-card">
                  <div class="preview-header">
                    <img v-if="playlistPreview.thumbnail" :src="playlistPreview.thumbnail" alt="" class="preview-thumb" />
                    <div v-else class="preview-thumb-fallback"><Music :size="32" /></div>
                    <div class="preview-info">
                      <h3>{{ playlistPreview.name }}</h3>
                      <p>{{ playlistPreview.track_count }} canciones • {{ playlistPreview.owner }}</p>
                    </div>
                  </div>

                  <div class="import-options">
                    <label>Importar a:</label>
                    <select v-model="selectedTargetId" class="target-select">
                      <option value="">Crear una nueva playlist</option>
                      <option v-for="pl in musicStore.playlists" :key="pl.id" :value="pl.id">
                        {{ pl.name }}
                      </option>
                    </select>
                  </div>

                  <div class="modal-footer">
                    <button class="cancel-btn" @click="playlistPreview = null">Cargar otra</button>
                    <button class="confirm-btn" @click="confirmImport">
                      {{ selectedTargetId ? '🔀 Unir Playlist' : '⬇️ Importar Todo' }}
                    </button>
                  </div>
                </div>

                <div v-else class="import-guide">
                  <div class="guide-icon"><Link :size="48" /></div>
                  <p>Pega el enlace de cualquier playlist de Spotify para importar sus canciones a tu biblioteca local.</p>
                </div>
              </div>

            </div>
          </Transition>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.modal-content {
  background: #1a1a1a;
  width: 100%;
  max-width: 500px;
  border-radius: 16px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.7);
  animation: modal-slide-up 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.06);
}

.modal-header {
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.tabs { display: flex; gap: 24px; }

.tabs button {
  background: transparent;
  padding: 8px 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: #b3b3b3;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tabs button.active { color: white; border-bottom-color: var(--spotify-green); }
.tabs button:disabled { opacity: 0.4; cursor: not-allowed; }

.close-btn { background: transparent; color: #b3b3b3; transition: color 0.2s; }
.close-btn:hover { color: white; }
.close-btn:disabled { opacity: 0.3; }

.modal-body { padding: 24px; }

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.input-group label { font-size: 0.8rem; font-weight: 700; color: white; }

.search-input-wrapper { display: flex; gap: 8px; }

.search-input-wrapper input {
  flex: 1;
  background: #2a2a2a;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  padding: 12px;
  color: white;
  font-size: 1rem;
}

.search-input-wrapper input:focus {
  outline: none;
  border-color: var(--spotify-green);
  background: #333;
}

.search-btn {
  background: #2a2a2a;
  width: 45px;
  height: 45px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #b3b3b3;
  border: 1px solid rgba(255,255,255,0.1);
}

.search-btn:hover { background: #3a3a3a; color: white; }

.preview-card {
  background: rgba(255,255,255,0.04);
  border-radius: 12px;
  padding: 16px;
  margin-top: 8px;
  animation: fade-in 0.3s ease;
  border: 1px solid rgba(255,255,255,0.06);
}

.preview-header { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
.preview-thumb { width: 64px; height: 64px; border-radius: 8px; object-fit: cover; }
.preview-thumb-fallback {
  width: 64px; height: 64px; background: #333;
  display: flex; align-items: center; justify-content: center;
  color: #555; border-radius: 8px;
}
.preview-info h3 { margin: 0; font-size: 1.1rem; color: white; }
.preview-info p { font-size: 0.8rem; color: #b3b3b3; margin-top: 4px; }

.import-options {
  border-top: 1px solid rgba(255,255,255,0.05);
  padding-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.import-options label { font-size: 0.8rem; font-weight: 700; color: #b3b3b3; }

.target-select {
  background: #2a2a2a;
  color: white;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.1);
  font-size: 0.9rem;
}

.import-guide { text-align: center; padding: 30px 0; color: #b3b3b3; }
.guide-icon { margin-bottom: 16px; opacity: 0.3; }
.import-guide p { font-size: 0.9rem; line-height: 1.5; }

.disclaimer { font-size: 0.75rem; color: #b3b3b3; line-height: 1.4; }

.modal-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 16px;
}

.cancel-btn {
  font-size: 0.9rem;
  font-weight: 700;
  color: white;
  background: transparent;
  padding: 12px 24px;
}

.confirm-btn {
  font-size: 0.9rem;
  font-weight: 700;
  color: black;
  background: var(--spotify-green);
  padding: 12px 32px;
  border-radius: 500px;
  transition: transform 0.2s, background 0.2s;
}

.confirm-btn:hover:not(:disabled) { transform: scale(1.04); background: #1fdf64; }
.confirm-btn:disabled { background: #535353; color: #b3b3b3; cursor: not-allowed; }

/* Confirm dialog */
.confirm-view {
  text-align: center;
  padding: 8px 0;
}

.confirm-icon {
  color: #facc15;
  margin-bottom: 16px;
  display: flex;
  justify-content: center;
}

.confirm-view h3 { margin: 0 0 12px; font-size: 1.2rem; color: white; }

.confirm-desc {
  font-size: 0.9rem;
  color: #b3b3b3;
  line-height: 1.6;
  margin-bottom: 4px;
}

.confirm-desc strong { color: white; }

/* Progress view */
.import-progress-view { padding: 8px 0; }

.importing-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  margin-bottom: 24px;
}

.importing-header h3 { margin: 0; font-size: 1.1rem; color: white; }

.current-track-label {
  font-size: 0.82rem;
  color: #b3b3b3;
  max-width: 380px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin: 0;
}

.spinner-ring {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(30, 215, 96, 0.2);
  border-top-color: var(--spotify-green);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.phase-badge {
  margin-top: 8px;
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 500px;
  font-size: 0.75rem;
  font-weight: 700;
  background: rgba(255,255,255,0.08);
  color: #b3b3b3;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  transition: background 0.3s, color 0.3s;
}

.phase-badge.phase-2 {
  background: rgba(30, 215, 96, 0.15);
  color: var(--spotify-green);
}

.progress-bar-wrap { margin-top: 8px; }

.progress-bar-track {
  width: 100%;
  height: 6px;
  background: rgba(255,255,255,0.1);
  border-radius: 6px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--spotify-green), #1fdf64);
  border-radius: 6px;
  transition: width 0.4s ease;
}

.progress-numbers {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 0.8rem;
  color: #b3b3b3;
}

.done-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  margin-bottom: 24px;
}

.done-icon {
  width: 56px;
  height: 56px;
  background: var(--spotify-green);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  color: black;
  font-weight: 700;
}

.done-header h3 { margin: 0; color: white; }
.done-header p { margin: 0; color: #b3b3b3; font-size: 0.9rem; }

.error-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  margin-bottom: 24px;
}

.error-icon { color: #ef4444; }
.error-header h3 { margin: 0; color: white; }
.error-header p { margin: 0; color: #b3b3b3; font-size: 0.9rem; }

.loader-small {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.1);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes modal-slide-up {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.3s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateX(10px); }
</style>
