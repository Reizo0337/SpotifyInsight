import { defineStore } from 'pinia'
import axios from 'axios'
import * as mockData from '../services/mockData'

const API_BASE = 'http://localhost:8000/api'
const MOCK_MODE = false 

// Typed state for better DX
interface MusicState {
  recentTracks: any[]
  userProfile: any
  stats: any
  isSyncing: boolean
  isSpotifyConnected: boolean
  lastSyncStatus: any
  recommendations: any[]
  searchResults: any[]
  isLoading: boolean
  nowPlaying: any
  queue: any[]
  currentIndex: number
  isShuffle: boolean
  shuffledQueue: any[]
  loopMode: 'off' | 'all' | 'one'
  streamUrl: string | null
  streamMeta: any
  isLoadingStream: boolean
  preloadedNext: { trackId: string, data: any } | null
  isPreloading: boolean
  streamCache: Map<string, { data: any, timestamp: number }>
  volume: number
  playbackRate: number
  persistedTime: number
  isReload: boolean
  shouldAutoResume: boolean
  isPlaying: boolean 
}

export const useMusicStore = defineStore('music', {
  state: (): MusicState => ({
    recentTracks: [],
    userProfile: null,
    stats: null,
    isSyncing: false,
    isSpotifyConnected: false,
    lastSyncStatus: null,
    recommendations: [],
    searchResults: [],
    isLoading: false,
    nowPlaying: null,
    queue: [],
    currentIndex: -1,
    isShuffle: false,
    shuffledQueue: [],
    loopMode: 'off',
    streamUrl: null,
    streamMeta: null,
    isLoadingStream: false,
    preloadedNext: null,
    isPreloading: false,
    streamCache: new Map(),
    volume: Number(localStorage.getItem('m-volume')) || 0.7,
    playbackRate: Number(localStorage.getItem('m-speed')) || 1,
    persistedTime: 0,
    isReload: (performance.getEntriesByType('navigation')[0] as any)?.type === 'reload',
    shouldAutoResume: false,
    isPlaying: false,
  }),

  getters: {
    hasData: (state) => !!(state.userProfile && state.stats),
    currentQueue: (state) => state.isShuffle ? state.shuffledQueue : state.queue,
    activeTrack: (state) => state.nowPlaying
  },

  actions: {
    async _apiCall(endpoint: string, params = {}, mock?: any, method = 'get', body?: any) {
      if (MOCK_MODE && mock !== undefined) return mock
      try {
        const config = { params }
        const { data } = method === 'post' 
          ? await axios.post(`${API_BASE}${endpoint}`, body, config)
          : await axios.get(`${API_BASE}${endpoint}`, config)
        return data
      } catch (err) {
        console.error(`API Error [${endpoint}]:`, err)
        return null
      }
    },

    async syncAccount() {
      this.isSyncing = true
      try {
        const data = await this._apiCall('/sync')
        if (data && data.status !== 'error') {
          this.lastSyncStatus = data
          await this.fetchAllData()
          return true
        }
        return false
      } finally {
        this.isSyncing = false
      }
    },

    async fetchAllData() {
      const [u, s, r, h, st] = await Promise.all([
        this._apiCall('/user-profile', {}, mockData.MOCK_USER_PROFILE),
        this._apiCall('/stats', {}, mockData.MOCK_STATS),
        this._apiCall('/recommendations', { limit: 20 }, mockData.MOCK_TRACKS.slice(0, 10)),
        this._apiCall('/history', { limit: 50 }, mockData.MOCK_TRACKS),
        this._apiCall('/status')
      ])
      if (u) this.userProfile = u
      if (s) this.stats = s
      if (r) this.recommendations = r
      if (h) this.recentTracks = h
      if (st) this.isSpotifyConnected = st.connected
    },

    async logTrackPlay(track: any) {
      if (!track) return
      // Prevent internal IDs (like "0") from being sent if possible
      const payload = {
          spotify_id: track.spotify_id || track.id,
          track_name: track.track_name,
          artist: track.artist,
          album: track.album,
          thumbnail: track.thumbnail,
          duration_ms: track.duration_ms
      }
      await this._apiCall('/music/played', {}, undefined, 'post', payload)
      // Refresh history silently
      const h = await this._apiCall('/history', { limit: 50 })
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
      const data = await this._apiCall('/search', { query }, [mockData.MOCK_TRACKS[0]])
      if (data) this.searchResults = data
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
        this.currentIndex = this.queue.findIndex(it => it.spotify_id === t?.spotify_id)
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
      const trackId = id || name
      this.isLoadingStream = true
      
      // 1. Preload hit?
      if (this.preloadedNext && this.preloadedNext.trackId === trackId) {
        this.streamUrl = this.preloadedNext.data.stream_url
        this.streamMeta = this.preloadedNext.data
        this.isLoadingStream = false
        this.preloadedNext = null
        this.preloadNext()
        return
      }

      // 2. Local session cache hit (30 min validity)
      const cached = this.streamCache.get(trackId)
      if (cached && (Date.now() - cached.timestamp < 30 * 60 * 1000)) {
        this.streamUrl = cached.data.stream_url
        this.streamMeta = cached.data
        this.isLoadingStream = false
        this.preloadNext()
        return
      }

      // 3. Remote fetch with race-condition protection
      this.streamUrl = null
      const currentTrackAtStart = this.nowPlaying?.spotify_id || this.nowPlaying?.id || this.nowPlaying?.track_name
      
      const data = await this._apiCall('/stream', { track: name, artist, spotify_id: id })
      
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
      if (!q.length || this.currentIndex === -1 || this.isPreloading) return
      
      const nextIdx = (this.currentIndex + 1) % q.length
      if (nextIdx === 0 && this.loopMode === 'off') return

      const t = q[nextIdx]
      const tid = t.spotify_id || t.id || t.track_name
      if (this.preloadedNext?.trackId === tid) return

      this.isPreloading = true
      const data = await this._apiCall('/stream', { 
        track: t.track_name, artist: t.artist || '', spotify_id: t.spotify_id || t.id 
      })
      if (data) this.preloadedNext = { trackId: tid, data }
      this.isPreloading = false
    }
  }
})
