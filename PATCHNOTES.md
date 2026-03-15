# Patch Notes - Spotify Wrapped Rework

## [2026-03-15] - Audio Player Excellence & Reliability

### Added
- **Dynamic Queue System**: Implemented a centralized queue management in Pinia (`musicStore`).
- **Transport Controls**: Full support for Next, Previous, Shuffle, and Loop (All/One/Off).
- **Audio Proxy Server**: Created a local backend proxy to bypass YouTube/Google CORS issues and enable seeking.
- **Smart Search Fallback**: Search now prioritizes Spotify metadata but automatically falls back to YouTube if rate-limited.
- **Enhanced Metadata**: Search results now include YouTube channel names (as album), high-quality thumbnails, and real track durations.
- **Remaining Time Display**: Player now shows a descending countdown for the current track.
- **Resilient Synchronization**: The `/sync` endpoint now handles Spotify rate limits gracefully, returning cached data instead of errors.

### Fixed
- **404 Streaming Errors**: Improved search robustness for tracks with complex titles or emojis by using multi-query logic.
- **Duration Mismatch**: Fixed the hardcoded "3:30" duration to reflect the actual media length.
- **Vite Compilation Errors**: Resolved duplicate `<script setup>` tags in `TrackRow.vue`.
- **Search Context**: Clicking a search result now correctly populates the playback queue with all results from that search.

### Changed
- **Premium UI Tweaks**: Removed rotating thumbnail animation for a cleaner, more modern look.
- **Thumbnail Reliability**: Replaced generic placeholders with dynamic art/shapes based on track data.
- **Performance**: Optimized backend streaming with better buffering and range request support.

---

### [2026-03-20] - Audio Player Evolution & Dynamic Queue
- **Dynamic Queue System:** Introduced a robust queue management system in Pinia.
- **Queue UI:** Added a sleek, blurred "Cola de Reproducción" overlay in the player.
- **Advanced Track Actions:**
  - New "Reproducir a continuación" (Play Next) feature.
  - New "Añadir a la cola" (Add to Queue) feature.
  - Context menu in search results for easy queueing.
- **Playback Polish:**
  - Real-time queue indices management.
  - Smooth transitions for the queue tray.
  - One-click track jumping from the queue list.
- **Architecture:** Decoupled context-based playback from on-the-fly queueing.

### [2026-03-19] - Streaming Stability & Design Polish
- **Audio Proxy:** Implemented a local backend proxy to bypass YouTube CORS restrictions.
- **Robust Searching:** Improved YouTube fallback logic to handle special characters and emojis.
- **Remaining Time:** Updated player to show a countdown timer for better UX.
- **Visual Cleanup:** Removed rotating thumbnail animation for a cleaner, modern look.
- **Resilient Sync:** Made Spotify sync more stable against rate limits (fallback to cache).
- **Metadata Quality:** Improved thumbnail resolution and album/channel display.

---

## [Initial Phases] - Project Foundation
- **Core Architecture**: Vue 3 + Pinia + FastAPI + Spotify API.
- **Audio Analysis Engine**: Integration with Librosa/Essentia for local "Vibe" matching.
- **Database Layer**: CSV-based data persistence for tracks and user history.
- **UI Design**: Modern "Glassmorphism" design system inspired by Spotify Premium.
