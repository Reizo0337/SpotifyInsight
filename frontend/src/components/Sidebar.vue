<script setup lang="ts">
import { Home, Search, Library, Layers, Heart, PlusSquare, Settings, Bell, RefreshCw } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import { useMusicStore } from '../stores/musicStore'

const musicStore = useMusicStore()
</script>

<template>
  <aside class="sidebar-2026">
    <div class="glass-container">
      <div class="logo-section">
        <div class="logo-glow"></div>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="#1565FF" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.49 17.29c-.22.35-.67.46-1.02.24-2.84-1.74-6.42-2.13-10.63-1.18-.4.09-.79-.16-.88-.55-.09-.4.16-.79.55-.88 4.62-1.05 8.58-.6 11.75 1.34.34.22.45.67.23 1.03zm1.46-3.26c-.27.44-.85.59-1.3.31-3.25-1.99-8.2-2.58-12.04-1.41-.5.15-1.02-.13-1.17-.63-.15-.5.13-1.02.63-1.17 4.41-1.34 9.87-.67 13.57 1.6.45.27.6.85.31 1.3zm.14-3.41c-3.9-2.31-10.32-2.53-14.07-1.39-.6.18-1.24-.16-1.42-.76-.18-.6.16-1.24.76-1.42 4.31-1.31 11.41-1.05 15.93 1.63.54.32.72 1.02.4 1.56-.32.54-1.02.72-1.6.4z"/>
        </svg>
        <div class="logo-text">
            <span class="brand">Spotify</span>
            <span class="sub-brand">INSIGHTS</span>
        </div>
      </div>

      <nav class="main-nav">
        <RouterLink to="/" class="nav-item">
          <div class="icon-wrap"><Home :size="20" /></div>
          <span>Explorar</span>
        </RouterLink>
        <RouterLink to="/search" class="nav-item">
          <div class="icon-wrap"><Search :size="20" /></div>
          <span>Buscar</span>
        </RouterLink>
        <RouterLink to="/wrapped" class="nav-item wrapped-link">
          <div class="icon-wrap"><Layers :size="20" /></div>
          <span>Insight Wrapped</span>
        </RouterLink>
      </nav>

      <div class="divider"></div>

      <div class="library-container">
        <div class="lib-header">
          <div class="title-group">
            <Library :size="20" />
            <span>Biblioteca</span>
          </div>
          <button class="add-btn"><PlusSquare :size="18" /></button>
        </div>
        <div class="lib-divider"></div>

        <div class="lib-content">
          <div class="list-item active">
            <div class="thumb heart-thumb">
                <Heart :size="14" fill="white" />
            </div>
            <div class="details">
              <p class="name">Me gusta</p>
              <p class="meta">Lista • {{ musicStore.stats?.total_tracks || 0 }} canciones</p>
            </div>
          </div>
          
          <div class="list-item">
            <div class="thumb synth-thumb">
                <Activity :size="14" />
            </div>
            <div class="details">
              <p class="name">Vibe Analysis</p>
              <p class="meta">Smart List</p>
            </div>
          </div>
        </div>
      </div>

      <div class="sidebar-footer">
        <button class="footer-icon btn-sync" 
                :class="{ 'active': musicStore.isSpotifyConnected, 'is-syncing': musicStore.isSyncing }" 
                :title="musicStore.isSpotifyConnected ? 'Sincronizar Spotify (Conectado)' : 'Spotify Desconectado - Click para intentar sincronizar'" 
                @click="musicStore.syncAccount" 
                :disabled="musicStore.isSyncing">
          <RefreshCw :size="20" :class="{ 'spin': musicStore.isSyncing }" />
          <div v-if="musicStore.isSpotifyConnected" class="status-dot online"></div>
          <div v-else class="status-dot offline"></div>
        </button>
        <button class="footer-icon"><Settings :size="20" /></button>
        <button class="footer-icon"><Bell :size="20" /></button>
        <div class="user-trigger">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Spotify" alt="User">
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar-2026 {
  grid-area: sidebar;
  display: flex;
  flex-direction: column;
  padding: 0;
  height: 100%;
  transition: all 0.3s ease;
}

@media (max-width: 768px) {
    .sidebar-2026 {
        display: none;
    }
}

.glass-container {
  height: 100%;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  padding: 24px 16px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

@media (max-width: 1024px) {
    .sidebar-2026 {
        width: 80px !important;
    }
    .glass-container {
        padding: 24px 8px;
        align-items: center;
    }
    /* Hide text labels and add-btn but keep icons */
    .logo-text, .nav-item span, .lib-header span, .add-btn, .details, .divider, .sidebar-footer button {
        display: none !important;
    }
    .nav-item {
        justify-content: center;
        align-items: center;
        padding: 12px;
        width: 48px;
        height: 48px;
    }
    .logo-section {
        margin-bottom: 24px;
        padding-left: 0;
        justify-content: center;
    }
    .main-nav {
        align-items: center;
    }

    /* Library section */
    .library-container {
        align-items: center;
        width: 100%;
        margin-top: 24px;
        padding-top: 24px;
        border-top: 1px solid var(--glass-border);
        gap: 8px;
    }
    .lib-divider {
        display: none !important;
    }
    /* Library header: center the icon; title-group handles flex */
    .lib-header {
        width: 64px;
        padding: 0;
        justify-content: center;
        margin-bottom: 4px;
    }
    .title-group {
        width: 100%;
        justify-content: center;
    }
    /* Show playlist items as icon-only thumbnails */
    .lib-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        width: 100%;
    }
    .list-item {
        justify-content: center;
        padding: 4px;
        width: 100%;
    }
    /* Bigger thumbs for visibility */
    .list-item .thumb {
        width: 52px;
        height: 52px;
        border-radius: 8px;
    }
    /* Hide text inside list items */
    .list-item .details {
        display: none !important;
    }
}

.logo-section {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 40px;
    padding-left: 8px;
    position: relative;
}

.logo-glow {
    position: absolute;
    width: 40px;
    height: 40px;
    background: var(--spotify-green);
    filter: blur(20px);
    opacity: 0.3;
    left: -5px;
}

.logo-text {
    display: flex;
    flex-direction: column;
    line-height: 1;
}

.logo-text .brand {
    font-weight: 900;
    font-size: 1.2rem;
    letter-spacing: -0.5px;
}

.logo-text .sub-brand {
    font-size: 0.6rem;
    letter-spacing: 2px;
    color: var(--spotify-green);
    font-weight: 700;
}

.main-nav {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 16px;
    border-radius: 12px;
    color: var(--spotify-text-grey);
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    line-height: normal;
}

.nav-item:hover {
    color: white;
    background: rgba(255,255,255,0.05);
}

.icon-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
}

.nav-item.router-link-active {
    color: white;
    background: rgba(255,255,255,0.1);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.1);
}

.nav-item.router-link-active::before {
    content: '';
    position: absolute;
    left: 0;
    width: 3px;
    height: 16px;
    background: var(--spotify-green);
    border-radius: 0 4px 4px 0;
}

.wrapped-link {
    margin-top: 8px;
    background: rgba(21, 101, 255, 0.1);
    color: var(--spotify-green);
    border: 1px solid rgba(21, 101, 255, 0.2);
}

.wrapped-link:hover {
    background: rgba(21, 101, 255, 0.2);
}

.lib-divider {
    height: 1px;
    background: rgba(255,255,255,0.05);
    margin: 8px 8px 16px 8px;
}

.divider {
    height: 1px;
    background: var(--glass-border);
    margin: 24px 0;
}

.library-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.lib-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 8px;
    color: var(--spotify-text-grey);
}

.title-group {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.9rem;
    font-weight: 700;
}

.add-btn {
    color: var(--spotify-text-grey);
    opacity: 0.6;
}

.add-btn:hover {
    opacity: 1;
    color: white;
}

.lib-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.list-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.list-item:hover {
    background: rgba(255,255,255,0.05);
}

.thumb {
    width: 44px;
    height: 44px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.heart-thumb {
    background: linear-gradient(135deg, #450af5, #c4efd9);
}

.synth-thumb {
    background: #282828;
    color: var(--spotify-neon);
}

.details .name {
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 2px;
}

.details .meta {
    font-size: 0.75rem;
    color: var(--spotify-text-grey);
}

.sidebar-footer {
    margin-top: auto;
    display: flex;
    align-items: center;
    gap: 16px;
    padding-top: 24px;
    border-top: 1px solid var(--glass-border);
}

.footer-icon {
    color: var(--spotify-text-grey);
}

.footer-icon:hover {
    color: white;
}

.user-trigger {
    margin-left: auto;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    overflow: hidden;
    border: 2px solid var(--glass-border);
    cursor: pointer;
}

.user-trigger img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.btn-sync {
    position: relative;
    transition: all 0.3s ease;
}

.btn-sync.active {
    color: var(--spotify-green);
}

.btn-sync:not(.active) {
    color: #ff9800;
}

.status-dot {
    position: absolute;
    top: -2px;
    right: -2px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    border: 1.5px solid #121212;
}

.status-dot.online {
    background: var(--spotify-green);
    box-shadow: 0 0 8px var(--spotify-green);
}

.status-dot.offline {
    background: #ff9800;
}

.spin {
    animation: rotate 1.5s linear infinite;
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
</style>
