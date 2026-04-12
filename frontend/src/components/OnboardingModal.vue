<script setup lang="ts">
import { ref, computed } from 'vue'
import { X, Check, Loader2, Sparkles, Music, Box, ChevronRight, AlertCircle, Headphones } from 'lucide-vue-next'
import { useMusicStore } from '../stores/musicStore'

const musicStore = useMusicStore()
const selectedPlaylists = ref<string[]>([])
const view = ref<'welcome' | 'select' | 'import' | 'done'>('welcome')

// Import tracking
const currentImportIndex = ref(0)
const importingName = ref('')
const importingStatus = ref('')
const importProgress = ref(0)
const hasErrors = ref(false)

const togglePlaylist = (id: string) => {
  const idx = selectedPlaylists.value.indexOf(id)
  if (idx > -1) selectedPlaylists.value.splice(idx, 1)
  else selectedPlaylists.value.push(id)
}

const startOnboardingImport = async () => {
  if (selectedPlaylists.value.length === 0) {
    await musicStore.completeOnboarding()
    return
  }

  view.value = 'import'
  const token = localStorage.getItem('nebula-token')

  for (let i = 0; i < selectedPlaylists.value.length; i++) {
    const plId = selectedPlaylists.value[i]
    const plData = musicStore.remotePlaylists.find(p => p.id === plId)
    if (!plData) continue

    currentImportIndex.value = i + 1
    importingName.value = plData.name
    importProgress.value = 0
    importingStatus.value = 'Iniciando misión en la nube...'

    try {
      // 1. Kick off the Job
      const startResp = await fetch(`http://localhost:8000/api/v1/playlists/import/start`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ url: plId, name: plData.name })
      })
      
      const { job_id } = await startResp.json()
      
      // 2. Poll for status
      let completed = false
      while (!completed) {
        const statusResp = await fetch(`http://localhost:8000/api/v1/playlists/import/status/${job_id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        const status = await statusResp.json()
        
        importingStatus.value = status.message || 'Sincronizando...'
        importProgress.value = status.progress || 0
        
        if (status.status === 'completed') {
            completed = true
        } else if (status.status === 'failed') {
            hasErrors.value = true
            throw new Error(status.error)
        }
        
        await new Promise(r => setTimeout(r, 1500))
      }
    } catch (e) {
      console.error('Onboarding import failed for', plData.name, e)
      hasErrors.value = true
    }
  }

  view.value = 'done'
  await musicStore.fetchPlaylists()
}

const finalize = async () => {
  await musicStore.completeOnboarding()
}
</script>

<template>
  <Transition name="nebula-modal">
    <div v-if="musicStore.isOnboardingModalOpen" class="onboarding-overlay" @click.self="selectedPlaylists.length === 0 && finalize()">
      <div class="onboarding-orb orb-1"></div>
      <div class="onboarding-orb orb-2"></div>

      <div class="onboarding-card glass">
        <div class="card-inner">
          
          <Transition name="view-fade" mode="out-in">
            <!-- VIEW: WELCOME -->
            <div v-if="view === 'welcome'" key="welcome" class="view-content welcome-view">
              <div class="hero-icon">
                <Sparkles :size="48" class="pulse-icon" />
              </div>
              <h1>Bienvenido a Nebula</h1>
              <p class="subtitle">Tu ecosistema musical ha sido inicializado con éxito.</p>
              
              <div class="features-list">
                <div class="feat">
                    <div class="feat-icon"><Music :size="20" /></div>
                    <div class="feat-text">
                        <strong>Señales Purificadas</strong>
                        <span>Streaming de alta fidelidad sin interrupciones.</span>
                    </div>
                </div>
                <div class="feat">
                    <div class="feat-icon"><Box :size="20" /></div>
                    <div class="feat-text">
                        <strong>Biblioteca Unificada</strong>
                        <span>Toda tu música de Spotify ahora bajo tu control.</span>
                    </div>
                </div>
              </div>

              <div class="footer-actions">
                <button class="nebula-btn primary" @click="view = 'select'">
                  Configurar mi Librería <ChevronRight :size="18" />
                </button>
              </div>
            </div>

            <!-- VIEW: SELECT PLAYLISTS -->
            <div v-else-if="view === 'select'" key="select" class="view-content select-view">
              <header class="view-header">
                <h2>Importación de Datos</h2>
                <p>Hemos detectado {{ musicStore.remotePlaylists.length }} colecciones en tu nube de Spotify. ¿Cuáles quieres transferir a Nebula?</p>
              </header>

              <div class="playlists-grid thin-scrollbar" v-if="musicStore.remotePlaylists.length > 0">
                <div 
                  v-for="pl in musicStore.remotePlaylists" 
                  :key="pl.id" 
                  class="pl-item"
                  :class="{ 'selected': selectedPlaylists.includes(pl.id) }"
                  @click="togglePlaylist(pl.id)"
                >
                  <div class="pl-thumb">
                    <img v-if="pl.thumbnail" :src="pl.thumbnail" alt="">
                    <Music v-else :size="24" />
                    <div class="check-overlay"><Check :size="20" /></div>
                  </div>
                  <div class="pl-meta">
                    <span class="pl-name">{{ pl.name }}</span>
                    <span class="pl-tracks">{{ pl.track_count }} pistas</span>
                  </div>
                </div>
              </div>
              <div v-else class="empty-playlists">
                <Loader2 :size="48" class="spin" v-if="musicStore.isLoading" />
                <div v-else class="no-playlists">
                  <AlertCircle :size="48" />
                  <p>No hemos encontrado colecciones o tu sesión ha expirado.</p>
                  <button class="nebula-btn secondary" @click="musicStore.fetchSpotifyPlaylists()">
                    Reintentar Escaneo
                  </button>
                </div>
              </div>

              <div class="footer-actions multi">
                <button class="nebula-btn secondary" @click="finalize">Omitir por ahora</button>
                <button class="nebula-btn primary" @click="startOnboardingImport" :disabled="selectedPlaylists.length === 0">
                  Importar {{ selectedPlaylists.length }} Colecciones
                </button>
              </div>
            </div>

            <!-- VIEW: IMPORTING -->
            <div v-else-if="view === 'import'" key="import" class="view-content import-view">
               <div class="loader-wrap">
                  <div class="frequency-bars">
                    <div v-for="i in 12" :key="i" class="bar" :style="{ '--delay': (i*0.1)+'s' }"></div>
                  </div>
               </div>
               <h3>Sincronizando Frecuencias...</h3>
               <p class="status-msg">{{ importingStatus || 'Conectando...' }}</p>
               <p class="progress-label">Importando: {{ importingName }} ({{ currentImportIndex }}/{{ selectedPlaylists.length }})</p>

               <div class="nebula-progress">
                  <div class="progress-track">
                    <div class="progress-fill" :style="{ width: importProgress + '%' }"></div>
                  </div>
                  <span class="pct">{{ importProgress }}%</span>
               </div>

               <div v-if="hasErrors" class="error-toast">
                  <AlertCircle :size="16" />
                  <span>Algunas señales podrían ser inestables. Continuando...</span>
               </div>
            </div>

            <!-- VIEW: DONE -->
            <div v-else-if="view === 'done'" key="done" class="view-content done-view">
                <div class="success-icon">
                    <Headphones :size="48" />
                </div>
                <h2>Sistema Listo</h2>
                <p>Tus colecciones han sido integradas en el núcleo de Nebula.</p>
                
                <div class="stats-box">
                    <div class="stat">
                        <span class="val">{{ selectedPlaylists.length }}</span>
                        <span class="lab">Colecciones</span>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat">
                        <span class="val">✓</span>
                        <span class="lab">Sincronizado</span>
                    </div>
                </div>

                <div class="footer-actions">
                  <button class="nebula-btn primary large" @click="finalize">
                    Entrar en Nebula
                  </button>
                </div>
            </div>
          </Transition>

        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.onboarding-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: rgba(4, 4, 6, 0.9);
  backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  overflow: hidden;
}

.onboarding-orb {
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.15;
  z-index: -1;
}
.orb-1 { top: -100px; left: -100px; background: var(--nebula-primary); }
.orb-2 { bottom: -100px; right: -100px; background: var(--nebula-accent); }

.onboarding-card {
  width: 100%;
  max-width: 580px;
  min-height: 480px;
  border-radius: 32px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 40px 100px rgba(0,0,0,0.8);
  position: relative;
  overflow: hidden;
}

.card-inner {
  padding: 48px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.view-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
}

h1, h2 {
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 12px;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 1.8rem; }

.subtitle {
  color: var(--nebula-text-dim);
  font-size: 1.1rem;
  margin-bottom: 40px;
}

/* Welcome View */
.hero-icon {
  margin-bottom: 32px;
  width: 80px;
  height: 80px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--nebula-primary);
}

.pulse-icon {
  animation: float 3s ease-in-out infinite;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 48px;
}

.feat {
  display: flex;
  gap: 20px;
}

.feat-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: rgba(255,255,255,0.03);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--nebula-accent);
}

.feat-text {
  display: flex;
  flex-direction: column;
}

.feat-text strong {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.feat-text span {
  font-size: 0.9rem;
  color: var(--nebula-text-muted);
}

/* Select View */
.view-header { margin-bottom: 32px; }
.view-header p { color: var(--nebula-text-dim); line-height: 1.6; }

.playlists-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-height: 320px;
  overflow-y: auto;
  margin-bottom: 32px;
  padding-right: 8px;
}

.pl-item {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 16px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.pl-item:hover {
  background: rgba(255,255,255,0.06);
  transform: translateY(-2px);
}

.pl-item.selected {
  background: rgba(99, 102, 241, 0.1);
  border-color: var(--nebula-primary);
}

.pl-thumb {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  position: relative;
  overflow: hidden;
  background: #111;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #444;
}

.pl-thumb img { width: 100%; height: 100%; object-fit: cover; }

.check-overlay {
  position: absolute;
  inset: 0;
  background: rgba(99, 102, 241, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.pl-item.selected .check-overlay { opacity: 1; }

.pl-meta { display: flex; flex-direction: column; min-width: 0; }
.pl-name {
  font-weight: 700;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}
.pl-tracks { font-size: 0.75rem; color: var(--nebula-text-muted); }

/* Import View */
.import-view {
  align-items: center;
  justify-content: center;
  text-align: center;
}

.loader-wrap {
  margin-bottom: 40px;
  height: 60px;
  display: flex;
  align-items: flex-end;
}

.frequency-bars {
  display: flex;
  gap: 4px;
  height: 100%;
}

.bar {
  width: 6px;
  background: var(--nebula-primary);
  border-radius: 3px;
  height: 20%;
  animation: barPulse 1s ease-in-out infinite alternate;
  animation-delay: var(--delay);
}

@keyframes barPulse {
  to { height: 100%; background: var(--nebula-accent); }
}

.status-msg { font-size: 1.2rem; margin-bottom: 8px; }
.progress-label { color: var(--nebula-text-dim); font-size: 0.9rem; margin-bottom: 32px; }

.nebula-progress {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 16px;
}

.progress-track {
  flex: 1;
  height: 8px;
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--nebula-primary), var(--nebula-accent));
  transition: width 0.4s cubic-bezier(0.1, 0.7, 1, 0.1);
  box-shadow: 0 0 15px rgba(99, 102, 241, 0.5);
}

.pct { font-family: 'JetBrains Mono', monospace; font-weight: 800; color: var(--nebula-accent); width: 45px; }

.error-toast {
  margin-top: 24px;
  padding: 10px 16px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 12px;
  color: #f87171;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Done View */
.done-view {
  align-items: center;
  justify-content: center;
  text-align: center;
}

.success-icon {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, var(--nebula-primary), var(--nebula-accent));
  border-radius: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 32px;
  box-shadow: 0 20px 40px rgba(99, 102, 241, 0.4);
}

.stats-box {
  display: flex;
  align-items: center;
  gap: 24px;
  background: rgba(255,255,255,0.04);
  padding: 20px 32px;
  border-radius: 20px;
  margin: 32px 0 48px;
}

.stat { display: flex; flex-direction: column; }
.stat .val { font-size: 1.5rem; font-weight: 800; color: white; }
.stat .lab { font-size: 0.75rem; color: var(--nebula-text-muted); text-transform: uppercase; letter-spacing: 1px; }

.stat-divider { width: 1px; height: 30px; background: rgba(255,255,255,0.1); }

/* Buttons */
.footer-actions {
  margin-top: auto;
  display: flex;
  justify-content: center;
}

.footer-actions.multi {
  justify-content: space-between;
  gap: 16px;
}

.nebula-btn {
  padding: 14px 28px;
  border-radius: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.nebula-btn.primary {
  background: var(--nebula-primary);
  color: white;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}

.nebula-btn.primary:hover {
  background: var(--nebula-accent);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
}

.nebula-btn.primary:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  transform: none;
}

.nebula-btn.secondary {
  background: rgba(255,255,255,0.05);
  color: var(--nebula-text-dim);
  border: 1px solid rgba(255,255,255,0.1);
}

.nebula-btn.secondary:hover {
  background: rgba(255,255,255,0.1);
  color: white;
}

.nebula-btn.large {
  padding: 18px 48px;
  font-size: 1.1rem;
}

/* Animations */
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.nebula-modal-enter-active, .nebula-modal-leave-active {
  transition: opacity 0.5s ease, backdrop-filter 0.5s ease;
}
.nebula-modal-enter-from, .nebula-modal-leave-to {
  opacity: 0;
  backdrop-filter: blur(0px);
}

.view-fade-enter-active, .view-fade-leave-active {
  transition: all 0.4s ease;
}
.view-fade-enter-from { opacity: 0; transform: translateX(20px); }
.view-fade-leave-to { opacity: 0; transform: translateX(-20px); }

.thin-scrollbar::-webkit-scrollbar { width: 4px; }
.thin-scrollbar::-webkit-scrollbar-track { background: transparent; }
.thin-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
</style>
