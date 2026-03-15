import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'
const MOCK_MODE = false // Set to false to use real backend

import * as mockData from '../services/mockData'

export const useMusicStore = defineStore('music', {
  state: () => ({
    recentTracks: [] as any[],
    userProfile: null as any,
    stats: null as any,
    isSyncing: false,
    lastSyncStatus: null as any,
    recommendations: [] as any[],
    searchResults: [] as any[],
    isLoading: false,
    nowPlaying: null as any,
    queue: [] as any[],
    currentIndex: -1,
    isShuffle: false,
    shuffledQueue: [] as any[],
    loopMode: 'off' as 'off' | 'all' | 'one',
    streamUrl: null as string | null,
    streamMeta: null as any,
    isLoadingStream: false,
  }),

  getters: {
    hasData: (state) => !!(state.userProfile && state.stats && state.recentTracks.length > 0),
    currentQueue: (state) => state.isShuffle ? state.shuffledQueue : state.queue
  },

  actions: {

    async syncAccount() {
      this.isSyncing = true
      try {
        if (MOCK_MODE) {
          await new Promise(resolve => setTimeout(resolve, 1000))
          this.lastSyncStatus = mockData.MOCK_SYNC_STATUS
          await this.fetchAllData()
          return mockData.MOCK_SYNC_STATUS
        }
        const { data } = await axios.get(`${API_BASE}/sync`)
        this.lastSyncStatus = data
        await this.fetchAllData()
        return data
      } catch (error) {
        console.error('Sync failed', error)
      } finally {
        this.isSyncing = false
      }
    },

    async fetchAllData() {
      await Promise.all([
        this.fetchProfile(),
        this.fetchStats(),
        this.fetchRecommendations('discovery'),
        this.fetchRecentTracks()
      ])
    },

    async fetchProfile() {
      try {
        if (MOCK_MODE) {
          this.userProfile = mockData.MOCK_USER_PROFILE
          return
        }
        const { data } = await axios.get(`${API_BASE}/user-profile`)
        this.userProfile = data
      } catch (error) {
        console.error('Profile fetch failed', error)
      }
    },

    async fetchStats() {
      try {
        if (MOCK_MODE) {
          this.stats = mockData.MOCK_STATS
          return
        }
        const { data } = await axios.get(`${API_BASE}/stats`)
        this.stats = data
      } catch (error) {
        console.error('Stats fetch failed', error)
      }
    },

    async fetchRecentTracks() {
      try {
        if (MOCK_MODE) {
          this.recentTracks = mockData.MOCK_TRACKS
          return
        }
        const { data } = await axios.get(`${API_BASE}/history`)
        this.recentTracks = data
      } catch (error) {
        console.error('History fetch failed', error)
      }
    },

    async fetchRecommendations(mode = 'vibe') {
      try {
        if (MOCK_MODE) {
          this.recommendations = mockData.MOCK_TRACKS.slice(0, 2)
          return
        }
        const { data } = await axios.get(`${API_BASE}/recommendations`, {
          params: { mode, limit: 20 }
        })
        this.recommendations = data
      } catch (error) {
        console.error('Recommendations failed', error)
      }
    },

    async search(query: string) {
      if (!query) return
      this.isLoading = true
      try {
        if (MOCK_MODE) {
          await new Promise(resolve => setTimeout(resolve, 500))
          this.searchResults = [mockData.MOCK_TRACKS[0]]
          return
        }
        const { data } = await axios.get(`${API_BASE}/search`, {
          params: { query }
        })
        this.searchResults = data
      } catch (error) {
        console.error('Search failed', error)
      } finally {
        this.isLoading = false
      }
    },

    setNowPlaying(track: any, contextQueue?: any[]) {
      this.nowPlaying = track
      
      if (contextQueue) {
        this.queue = contextQueue
        // Matching by ID is preferred, but fallback to name+artist for safety
        this.currentIndex = contextQueue.findIndex(t => 
          (t.spotify_id && track.spotify_id && t.spotify_id === track.spotify_id) || 
          (t.id && track.id && t.id === track.id) ||
          (t.track_name === track.track_name && t.artist === track.artist)
        )
        if (this.isShuffle) {
          this.shuffleQueue()
        }
      }

      // Auto-stream when a track is selected (only in live mode)
      if (!MOCK_MODE && track?.track_name) {
        this.streamTrack(track.track_name, track.artist || '')
      }
    },

    addToQueue(track: any) {
      this.queue.push(track)
      if (this.isShuffle) {
        this.shuffledQueue.push(track)
      }
      if (this.currentIndex === -1) {
        this.setNowPlaying(track)
      }
    },

    insertNext(track: any) {
      if (this.currentIndex === -1) {
        this.setNowPlaying(track)
        return
      }
      
      const insertPos = this.currentIndex + 1
      this.queue.splice(insertPos, 0, track)
      if (this.isShuffle) {
        this.shuffledQueue.splice(insertPos, 0, track)
      }
    },

    removeFromQueue(index: number) {
      this.queue.splice(index, 1)
      if (this.isShuffle) {
        this.shuffledQueue.splice(index, 1) // Note: This might not be perfectly mapped
      }
      if (index < this.currentIndex) {
        this.currentIndex--
      } else if (index === this.currentIndex) {
        this.playNext()
      }
    },

    playNext() {
      const q = this.currentQueue
      if (q.length === 0) return

      let nextIndex = this.currentIndex + 1
      if (nextIndex >= q.length) {
        if (this.loopMode === 'all') {
          nextIndex = 0
        } else {
          return // End of queue
        }
      }
      
      this.currentIndex = nextIndex
      const nextTrack = q[nextIndex]
      this.nowPlaying = nextTrack
      this.streamTrack(nextTrack.track_name, nextTrack.artist || '')
    },

    playPrevious() {
      const q = this.currentQueue
      if (q.length === 0) return

      let prevIndex = this.currentIndex - 1
      if (prevIndex < 0) {
        if (this.loopMode === 'all') {
          prevIndex = q.length - 1
        } else {
          prevIndex = 0 // Stay at first track
        }
      }

      this.currentIndex = prevIndex
      const prevTrack = q[prevIndex]
      this.nowPlaying = prevTrack
      this.streamTrack(prevTrack.track_name, prevTrack.artist || '')
    },

    toggleShuffle() {
      this.isShuffle = !this.isShuffle
      if (this.isShuffle) {
        this.shuffleQueue()
      }
    },

    shuffleQueue() {
      const newShuffle = [...this.queue]
      // Keep current track at index 0 or find it
      const currentTrack = this.nowPlaying
      const filtered = newShuffle.filter(t => t.spotify_id !== currentTrack?.spotify_id)
      
      for (let i = filtered.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [filtered[i], filtered[j]] = [filtered[j], filtered[i]];
      }
      
      if (currentTrack) {
        this.shuffledQueue = [currentTrack, ...filtered]
        this.currentIndex = 0
      } else {
        this.shuffledQueue = filtered
        this.currentIndex = 0
      }
    },

    toggleLoop() {
      const modes: ('off' | 'all' | 'one')[] = ['off', 'all', 'one']
      const currentIdx = modes.indexOf(this.loopMode)
      this.loopMode = modes[(currentIdx + 1) % modes.length]
    },

    async streamTrack(trackName: string, artist: string) {
      this.isLoadingStream = true
      this.streamUrl = null
      this.streamMeta = null
      try {
        const { data } = await axios.get(`${API_BASE}/stream`, {
          params: { track: trackName, artist },
          timeout: 15000 // 15s timeout
        })
        this.streamUrl = data.stream_url
        this.streamMeta = data
      } catch (error) {
        console.error('Stream failed', error)
        this.streamUrl = null
      } finally {
        this.isLoadingStream = false
      }
    },

    clearSearch() {
        this.searchResults = []
    }
  }
})
