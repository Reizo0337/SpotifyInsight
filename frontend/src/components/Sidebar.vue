<script setup lang="ts">
import { Home, Search, Library, Layers, Heart, PlusSquare, Settings, Bell, RefreshCw } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import { useMusicStore } from '../stores/musicStore'

const musicStore = useMusicStore()

const createNewPlaylist = async () => {
  musicStore.isCreateModalOpen = true
}
</script>

<template>
  <aside class="sidebar-nebula">
    <div class="glass-container">
      <div class="logo-section">
        <div class="logo-glow"></div>
        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="var(--nebula-primary)"/>
          <path d="M2 12L12 17L22 12" stroke="var(--nebula-accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M2 17L12 22L22 17" stroke="var(--nebula-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div class="logo-text">
            <span class="brand">NEBULA</span>
            <span class="sub-brand">CORE SYSTEM</span>
        </div>
      </div>

      <nav class="main-nav">
        <RouterLink to="/" class="nav-item" active-class="active">
          <div class="icon-wrap"><Home :size="20" /></div>
          <span>Home</span>
        </RouterLink>
        <RouterLink to="/search" class="nav-item" active-class="active">
          <div class="icon-wrap"><Search :size="20" /></div>
          <span>Search songs</span>
        </RouterLink>
        <RouterLink to="/wrapped" class="nav-item wrapped-link" active-class="active">
          <div class="icon-wrap"><Layers :size="20" /></div>
          <span>Tu Wrapped</span>
        </RouterLink>
      </nav>

      <div class="section-label">TU BIBLIOTECA</div>

      <div class="library-container">
        <div class="lib-header">
          <div class="title-group">
            <Library :size="18" />
            <span>Colecciones</span>
          </div>
          <button class="add-btn" @click="createNewPlaylist" title="Nueva Colección"><PlusSquare :size="18" /></button>
        </div>

        <div class="lib-content">
          <RouterLink to="/collection/tracks" class="list-item" active-class="active">
            <div class="thumb heart-thumb">
                <Heart :size="14" fill="white" />
            </div>
            <div class="details">
              <p class="name">Señales Favoritas</p>
              <p class="meta">{{ musicStore.favorites?.length || 0 }} pistas</p>
            </div>
          </RouterLink>
          
          <RouterLink v-for="playlist in musicStore.playlists" :key="playlist.id" :to="'/playlist/' + playlist.id" class="list-item" active-class="active">
            <div class="thumb playlist-thumb">
                <img v-if="playlist.thumbnail" :src="playlist.thumbnail" class="thumb-img" />
                <Library v-else :size="14" />
            </div>
            <div class="details">
              <p class="name">{{ playlist.name }}</p>
              <p class="meta">{{ playlist.tracks?.length || 0 }} archivos</p>
            </div>
          </RouterLink>
        </div>
      </div>

      <div class="sidebar-footer">
        <button class="footer-icon btn-sync" 
                :class="{ 'active': musicStore.isSpotifyConnected, 'is-syncing': musicStore.isSyncing }" 
                @click="musicStore.syncAccount" 
                :disabled="musicStore.isSyncing">
          <RefreshCw :size="18" :class="{ 'spin': musicStore.isSyncing }" />
        </button>
        <button v-if="musicStore.isSpotifyConnected" class="footer-icon" @click="musicStore.resetOnboarding" title="Reiniciar Setup">
          <Layers :size="18" />
        </button>
        <button class="footer-icon"><Bell :size="18" /></button>
        <button class="footer-icon"><Settings :size="18" /></button>
        
        <div class="user-profile">
            <img :src="`https://api.dicebear.com/7.x/identicon/svg?seed=${musicStore.userProfile?.username || 'nebula'}`" alt="User">
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar-nebula {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px;
  z-index: 100;
}

.glass-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px 12px;
  position: relative;
}

.logo-section {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 48px;
    padding-left: 8px;
}

.logo-glow {
    position: absolute;
    width: 60px;
    height: 60px;
    background: var(--nebula-primary);
    filter: blur(40px);
    opacity: 0.2;
    top: 20px;
    left: 20px;
}

.logo-text {
    display: flex;
    flex-direction: column;
}

.logo-text .brand {
    font-weight: 800;
    font-size: 1.3rem;
    letter-spacing: 2px;
    color: white;
}

.logo-text .sub-brand {
    font-size: 0.65rem;
    letter-spacing: 1px;
    color: var(--nebula-accent);
    font-weight: 600;
    opacity: 0.8;
}

.main-nav {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 32px;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 14px;
    border-radius: 14px;
    color: var(--nebula-text-dim);
    text-decoration: none;
    font-weight: 600;
    font-size: 0.95rem;
    transition: all 0.3s ease;
}

.nav-item:hover {
    color: white;
    background: var(--nebula-surface-hover);
    transform: translateX(4px);
}

.nav-item.active {
    color: white;
    background: var(--nebula-surface);
    border: 1px solid var(--glass-border);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.icon-wrap {
    color: var(--nebula-primary);
    display: flex;
    align-items: center;
    justify-content: center;
}

.nav-item.active .icon-wrap {
    filter: drop-shadow(0 0 8px var(--nebula-primary));
}

.wrapped-link {
    background: linear-gradient(90deg, rgba(99, 102, 241, 0.1), transparent);
    border: 1px dashed rgba(99, 102, 241, 0.3);
}

.section-label {
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: var(--nebula-text-muted);
    margin: 0 0 16px 12px;
}

.library-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
}

.lib-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 12px;
    margin-bottom: 12px;
    color: var(--nebula-text-dim);
}

.title-group {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.85rem;
    font-weight: 700;
}

.add-btn {
    color: var(--nebula-text-dim);
    opacity: 0.6;
    transition: all 0.2s;
}

.add-btn:hover {
    opacity: 1;
    color: var(--nebula-accent);
    transform: rotate(90deg);
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
    padding: 10px 12px;
    border-radius: 12px;
    text-decoration: none;
    color: var(--nebula-text-dim);
    transition: all 0.2s;
}

.list-item:hover {
    background: var(--nebula-surface-hover);
    color: white;
}

.list-item.active {
    background: rgba(255, 255, 255, 0.03);
    color: white;
}

.thumb {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.heart-thumb {
    background: linear-gradient(135deg, var(--nebula-primary), var(--nebula-accent));
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.playlist-thumb {
    background: #111;
    border: 1px solid var(--glass-border);
    color: var(--nebula-text-muted);
}

.thumb-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 10px;
}

.details .name {
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 2px;
}

.details .meta {
    font-size: 0.7rem;
    color: var(--nebula-text-muted);
}

.sidebar-footer {
    padding-top: 20px;
    margin-top: 20px;
    margin-bottom: 70px; /* SPACE FOR PLAYER */
    border-top: 1px solid var(--glass-border);
    display: flex;
    align-items: center;
    gap: 12px;
}

.footer-icon {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    color: var(--nebula-text-dim);
    background: var(--nebula-surface);
    transition: all 0.2s;
}

.footer-icon:hover {
    background: var(--nebula-surface-hover);
    color: white;
}

.btn-sync.active {
    color: var(--nebula-accent);
    box-shadow: 0 0 10px rgba(34, 211, 238, 0.2);
}

.user-profile {
    margin-left: auto;
    width: 38px;
    height: 38px;
    border-radius: 50%;
    border: 2px solid var(--nebula-primary);
    padding: 2px;
    cursor: pointer;
    transition: transform 0.2s;
}

.user-profile:hover {
    transform: scale(1.1);
}

.user-profile img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: cover;
}

.spin {
    animation: rotate 2s linear infinite;
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@media (max-width: 1024px) {
  .sidebar-nebula { width: 80px; padding: 10px; }
  .logo-text, .nav-item span, .section-label, .lib-header span, .add-btn, .details { display: none; }
  .nav-item, .list-item { justify-content: center; padding: 12px; }
  .logo-section { justify-content: center; padding: 0; }
  .sidebar-footer { flex-direction: column; align-items: center; }
  .user-profile { margin-left: 0; }
}
</style>
