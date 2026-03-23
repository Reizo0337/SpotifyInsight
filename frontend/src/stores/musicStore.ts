import { defineStore } from 'pinia'
import axios from 'axios'
import * as mockData from '../services/mockData'

const API_BASE = 'http://localhost:8000/api'
const MOCK_MODE = false 

// Typed state for better DX
// Typed state for better DX - placeholder for expansion

export const useMusicStore = defineStore('music', {
  state: (): any => ({
    accessToken: localStorage.getItem('nebula-token'),
    userProfile: null,
    stats: null,
    recommendations: [],
    recentTracks: [],
    isSpotifyConnected: false,
    favorites: [],
    playlists: [],
    searchResults: [],
    
    // Playback
    nowPlaying: null,
    queue: [],
    currentIndex: -1,
    isShuffle: false,
    shuffledQueue: [],
    loopMode: 'off',
    isPlaying: false,
    volume: Number(localStorage.getItem('m-volume')) || 0.7,
    playbackRate: Number(localStorage.getItem('m-speed')) || 1.0,
    persistedTime: Number(localStorage.getItem('m-time')) || 0,
    
    // UI / Loading
    isLoading: false,
    isLoadingStream: false,
    streamUrl: null,
    streamMeta: null,
    isReload: true,
    shouldAutoResume: false,
    isCreateModalOpen: false,

    // Stream Caching & Preloading
    streamCache: new Map(),
    preloadedNext: null,
    isPreloading: false,
    isSyncing: false
  }),

  getters: {
    currentQueue: (state) => {
      return state.isShuffle ? state.shuffledQueue : state.queue
    },
    activeTrack: (state) => state.nowPlaying
  },

  actions: {
    async _apiCall(endpoint: string, params = {}, method: 'get' | 'post' | 'delete' = 'get', body?: any, mock?: any) {
      if (MOCK_MODE && mock !== undefined) return mock
      
      const publicEndpoints = ['/auth/login', '/auth/register']
      if (!this.accessToken && !publicEndpoints.includes(endpoint)) {
        // Strictly block all unauthorized transmissions for cosmic safety
        return null
      }

      try {
        const url = `${API_BASE}${endpoint}`
        const config: any = { params, headers: {} }
        
        if (this.accessToken) {
          config.headers['Authorization'] = `Bearer ${this.accessToken}`
        }
        
        let res;
        if (method === 'post') {
          res = await axios.post(url, body, config)
        } else if (method === 'delete') {
          res = await axios.delete(url, config)
        } else {
          res = await axios.get(url, config)
        }
        return res.data
      } catch (err: any) {
        if (err.response?.status === 401) {
          this.logout()
        }
        console.error(`API Error [${method.toUpperCase()} ${endpoint}]:`, err)
        return null
      }
    },

    async login(credentials: any) {
      const form = new FormData()
      form.append('username', credentials.username)
      form.append('password', credentials.password)
      
      const data = await this._apiCall('/auth/login', {}, 'post', form)
      if (data && data.access_token) {
        this.accessToken = data.access_token
        localStorage.setItem('nebula-token', data.access_token)
        await this.fetchAllData()
        return true
      }
      return false
    },

    async register(userData: any) {
      const data = await this._apiCall('/auth/register', {}, 'post', userData)
      if (data && data.access_token) {
        this.accessToken = data.access_token
        localStorage.setItem('nebula-token', data.access_token)
        await this.fetchAllData()
        return true
      }
      return false
    },

    logout() {
      this.accessToken = null
      localStorage.removeItem('nebula-token')
      // Only redirect if not already on an auth page, to avoid loops
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login'
      }
    },

    async fetchAllData() {
      // Re-route to modular endpoints
      const [u, s, r, h, st] = await Promise.all([
        this._apiCall('/auth/me'),
        this._apiCall('/music/stats'),
        this._apiCall('/music/recommendations', { limit: 20 }),
        this._apiCall('/music/history', { limit: 50 }),
        this._apiCall('/music/status')
      ])
      if (u) this.userProfile = u
      if (s) this.stats = s
      if (r) this.recommendations = r
      if (h) this.recentTracks = h
      if (st) this.isSpotifyConnected = st.connected
    },

    async connectSpotify() {
      // Fetch the login URL and redirect
      const data = await this._apiCall('/auth/spotify/login')
      if (data && data.url) {
        window.location.href = data.url
      }
    },

    async syncAccount() {
      this.isSyncing = true
      try {
        const res = await this._apiCall('/music/sync')
        if (res && res.status === 'started') {
          // Continuous orbital monitoring (Polling)
          let isDone = false
          while (!isDone) {
            await new Promise(resolve => setTimeout(resolve, 3000))
            const status = await this._apiCall('/music/sync/status')
            if (status && status.status === 'completed') {
              isDone = true
            } else if (status && (status.status === 'idle' || status.status === 'error')) {
              break
            }
          }
          await this.fetchAllData()
        } else if (res && res.status === 'success') {
          await this.fetchAllData()
        }
      } catch (e) {
        console.error("Sync failed:", e)
      } finally {
        this.isSyncing = false
      }
    },

    async logTrackPlay(track: any) {
      if (!track || !this.accessToken) return
      const sid = track.spotify_id || track.id
      await this._apiCall(`/music/played`, { spotify_id: sid }, 'post')
      const h = await this._apiCall('/music/history', { limit: 50 })
      if (h) this.recentTracks = h
    },

    // Persistence
    savePlaybackState(isPlaying: boolean = false) {
      this.isPlaying = isPlaying
      const state = {
        nowPlaying: this.nowPlaying,
        trackId: this.nowPlaying?.spotify_id || this.nowPlaying?.id,
        queue: this.queue,
        currentIndex: this.currentIndex,
        isShuffle: this.isShuffle,
        shuffledQueue: this.shuffledQueue,
        loopMode: this.loopMode,
        wasPlaying: isPlaying
      }
      localStorage.setItem('m-playback-state', JSON.stringify(state))
    },

    getState(): boolean {
      const saved = localStorage.getItem('m-playback-state')
      if (!saved) return this.isPlaying
      try {
        const p = JSON.parse(saved)
        return p.wasPlaying || false
      } catch { return false }
    },

    loadPlaybackState() {
      const saved = localStorage.getItem('m-playback-state')
      if (!saved) return
      try {
        const p = JSON.parse(saved)
        Object.assign(this, {
          nowPlaying: p.nowPlaying,
          queue: p.queue || [],
          currentIndex: p.currentIndex ?? -1,
          isShuffle: !!p.isShuffle,
          shuffledQueue: p.shuffledQueue || [],
          loopMode: p.loopMode || 'off'
        })
        
        // Auto-resume if it was a reload and was playing
        if (this.isReload && p.wasPlaying) {
          this.shouldAutoResume = true
          this.isPlaying = true
        }

        if (this.nowPlaying && !this.streamUrl) {
          const t = this.nowPlaying
          this.streamTrack(t.track_name, t.artist, t.spotify_id || t.id)
        }
      } catch (e) {
        console.warn('Restore session failed', e)
      }
    },

    updateVolume(v: number) {
      this.volume = v
      localStorage.setItem('m-volume', v.toString())
    },

    updatePlaybackRate(r: number) {
      this.playbackRate = r
      localStorage.setItem('m-speed', r.toString())
    },

    updatePersistedTime(t: number) {
      this.persistedTime = t
      // Debounced or threshold-based save could be done here, 
      // but for simple app, direct save is okay.
      localStorage.setItem('m-time', t.toString())
    },

    async search(query: string) {
      if (!query) return
      this.isLoading = true
      const data = await this._apiCall('/music/search', { q: query })
      if (data) {
        this.searchResults = data
      }
      this.isLoading = false
    },

    // Playback control
    setNowPlaying(track: any, contextQueue?: any[]) {
      this.nowPlaying = track
      this.isPlaying = true // User explicitly started a track
      if (contextQueue) {
        this.queue = [...contextQueue]
        this.currentIndex = contextQueue.findIndex(t => 
          (t.spotify_id && t.spotify_id === track.spotify_id) || 
          (t.id && t.id === track.id) || 
          (t.track_name === track.track_name && t.artist === track.artist)
        )
        if (this.isShuffle) this.shuffleQueue()
      }
      if (!MOCK_MODE && track?.track_name) {
        this.streamTrack(track.track_name, track.artist || '', track.spotify_id || track.id)
      }
      this.savePlaybackState(true)
    },

    addToQueue(track: any) {
      this.queue.push(track)
      if (this.isShuffle) this.shuffledQueue.push(track)
      if (this.currentIndex === -1) this.setNowPlaying(track)
      this.savePlaybackState(this.isPlaying)
    },

    insertNext(track: any) {
      if (this.currentIndex === -1) return this.setNowPlaying(track)
      const pos = this.currentIndex + 1
      this.queue.splice(pos, 0, track)
      if (this.isShuffle) this.shuffledQueue.splice(pos, 0, track)
      this.savePlaybackState(this.getState())
    },

    playNext() {
      const q = this.currentQueue
      if (!q.length) return
      let next = this.currentIndex + 1
      if (next >= q.length) {
        if (this.loopMode === 'all') next = 0
        else return
      }
      this._changeTrack(next)
      this.fetchPlaylists()
      this.fetchFavorites()
    },

    async init() {
      // Inicia la aplicación cargando todos los datos necesarios
      if (this.isReload) {
        // if reload, maybe we want to do something specific
      }
      await this.fetchAllData()
      await this.fetchPlaylists()
      await this.fetchFavorites()
    },

    async fetchPlaylists() {
      try {
        const data = await this._apiCall('/playlists/')
        if (data) this.playlists = data
      } catch (e) {
        console.error('Fetch playlists failed', e)
      }
    },


    async fetchSpotifyPlaylistInfo(url: string) {
      return await this._apiCall(`/spotify/playlist-info?url=${encodeURIComponent(url)}`)
    },

    async importSpotifyPlaylist(playlistId: string, name: string, targetPlaylistId: string | null = null) {
      await this._apiCall('/spotify/playlists/import', {}, 'post', { 
        playlist_id: playlistId, 
        name,
        target_playlist_id: targetPlaylistId 
      })
      await this.fetchPlaylists()
    },

    async fetchFavorites() {
      try {
        const data = await this._apiCall('/music/favorites')
        if (data) this.favorites = data
      } catch (e) {
        console.error('Fetch favorites failed', e)
      }
    },

    async createPlaylist(name: string, isPublic: boolean = true) {
      try {
        const resp = await this._apiCall('/playlists', {}, 'post', { name, is_public: isPublic })
        if (resp) {
          this.playlists.push(resp)
          return resp
        }
      } catch (e) {
        console.error('Create playlist failed', e)
      }
      return null
    },

    async toggleFavorite(track: any) {
      try {
        const sid = track.spotify_id || track.id
        const resp = await this._apiCall('/music/favorites/toggle', { spotify_id: sid }, 'post')
        if (resp) {
          if (resp.is_favorite) {
            this.favorites.unshift(track)
          } else {
            this.favorites = this.favorites.filter((t: any) => t.spotify_id !== track.spotify_id)
          }
          return resp.is_favorite
        }
      } catch (e) {
        console.error('Toggle favorite failed', e)
      }
      return false
    },

    async addTrackToPlaylist(playlistId: string, track: any) {
      try {
        const resp = await this._apiCall(`/playlists/${playlistId}/tracks`, {}, 'post', track)
        if (resp && resp.status === 'success') {
          const pl = this.playlists.find(p => p.id === playlistId)
          if (pl && !pl.tracks.includes(track.spotify_id)) {
            pl.tracks.push(track.spotify_id)
          }
          return true
        }
      } catch (e) {
        console.error('Add to playlist failed', e)
      }
      return false
    },

    async removeTrackFromPlaylist(playlistId: string, spotifyId: string) {
      try {
        const resp = await this._apiCall(`/playlists/${playlistId}/tracks/${spotifyId}`, {}, 'delete')
        if (resp && resp.status === 'success') {
          const pl = this.playlists.find(p => p.id === playlistId)
          if (pl) {
            pl.tracks = pl.tracks.filter((id: string) => id !== spotifyId)
          }
          return true
        }
      } catch (e) {
        console.error('Remove from playlist failed', e)
      }
      return false
    },

    playPrevious() {
      const q = this.currentQueue
      if (!q.length) return
      let prev = this.currentIndex - 1
      if (prev < 0) {
        if (this.loopMode === 'all') prev = q.length - 1
        else prev = 0
      }
      this._changeTrack(prev)
    },

    _changeTrack(index: number) {
      this.currentIndex = index
      const t = this.currentQueue[index]
      this.nowPlaying = t
      this.streamTrack(t.track_name, t.artist || '', t.spotify_id || t.id)
      this.savePlaybackState(true) // We are definitely switching to play
    },

    toggleShuffle() {
      this.isShuffle = !this.isShuffle
      if (this.isShuffle) this.shuffleQueue()
      else {
        const t = this.nowPlaying
        this.currentIndex = this.queue.findIndex((it: any) => it.spotify_id === t?.spotify_id)
      }
      this.savePlaybackState(this.getState())
    },

    shuffleQueue() {
      const arr = [...this.queue]
      const cur = this.nowPlaying
      const filtered = arr.filter(t => t.spotify_id !== cur?.spotify_id)
      // Fisher-Yates
      for (let i = filtered.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [filtered[i], filtered[j]] = [filtered[j], filtered[i]]
      }
      this.shuffledQueue = cur ? [cur, ...filtered] : filtered
      this.currentIndex = 0
    },

    toggleLoop() {
      const m: any[] = ['off', 'all', 'one']
      this.loopMode = m[(m.indexOf(this.loopMode) + 1) % 3]
      this.savePlaybackState(this.getState())
    },

    async streamTrack(name: string, artist: string, id?: string) {
      if (!this.accessToken) return // Block playback if unauthorized
      const trackId = id || name
      this.isLoadingStream = true
      
      // 1. Preload hit?
      if (this.preloadedNext && this.preloadedNext.trackId === trackId) {
        this.streamUrl = this.preloadedNext.data.url // Backend uses "url"
        this.streamMeta = this.preloadedNext.data
        this.isLoadingStream = false
        this.preloadedNext = null
        this.preloadNext()
        return
      }

      // 2. Local session cache hit (30 min validity)
      const cached = this.streamCache.get(trackId)
      if (cached && (Date.now() - cached.timestamp < 30 * 60 * 1000)) {
        this.streamUrl = cached.data.url
        this.streamMeta = cached.data
        this.isLoadingStream = false
        this.preloadNext()
        return
      }

      // 3. Remote fetch with race-condition protection
      this.streamUrl = null
      const currentTrackAtStart = this.nowPlaying?.spotify_id || this.nowPlaying?.id || this.nowPlaying?.track_name
      
      const params: any = {}
      if (id) params.spotify_id = id
      if (name) params.track_name = name
      if (artist) params.artist = artist

      const data = await this._apiCall('/music/stream', params)
      
      // Only update if we haven't switched to another track during the wait
      const currentTrackNow = this.nowPlaying?.spotify_id || this.nowPlaying?.id || this.nowPlaying?.track_name
      if (data && currentTrackAtStart === currentTrackNow) {
        this.streamUrl = data.stream_url
        this.streamMeta = data
        this.streamCache.set(trackId, { data, timestamp: Date.now() })
        this.preloadNext()
      }
      this.isLoadingStream = false
    },

    async preloadNext() {
      const q = this.currentQueue
      if (!q || !q.length || this.currentIndex === -1 || this.isPreloading) return
      
      const nextIdx = (this.currentIndex + 1) % q.length
      if (nextIdx === 0 && this.loopMode === 'off') return

      const t = q[nextIdx]
      const tid = t.spotify_id || t.id || t.track_name
      if (this.preloadedNext?.trackId === tid) return

      this.isPreloading = true
      const params: any = {}
      if (t.spotify_id || t.id) params.spotify_id = t.spotify_id || t.id
      if (t.track_name) params.track_name = t.track_name
      if (t.artist) params.artist = t.artist

      const data = await this._apiCall('/music/stream', params)
      if (data) this.preloadedNext = { trackId: tid, data }
      this.isPreloading = false
    }
  }
})
