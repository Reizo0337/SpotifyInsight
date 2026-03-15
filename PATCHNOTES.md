# Patch Notes - Spotify Wrapped Rework

## [2026-03-22] - Expert Refactoring & Persistent Streaming
### Added
- **Persistent Stream Database**: Resolved audio links are now saved in `saved_tracks.csv` with their expiration dates. 
- **Instant Playback**: The player now uses the persistent database to skip the YouTube API call if a valid link exists (0ms delay).
- **Auto-Library Registration**: Playing songs from search results now automatically registers them in your persistent library for future fast access.
- **Zero-Latency Streaming**: Implemented multi-level caching (Frontend & Backend) to avoid redundant YouTube resolutions.
- **Concurrency Protection**: Added a backend semaphore and thread-offloading for `yt-dlp`, preventing server hangs.
- **Auto-resume on F5**: Detected page reloads (F5) to automatically replay music if it was playing before.

### Changed
- **Backend Architecture**: Consolidated API controllers and services for better maintainability and reduced complexity.
- **Store Modularization**: Refactored Pinia `musicStore` with a centralized API helper, typed state, and refined queue logic.
- **Player UI Smoothness**: Overhauled the progress bar and slider logic to eliminate "jumping".

### Fixed
- **Recommendation Engine**: Resolved core logic bugs where coroutines were incorrectly handled.
- **Type Safety**: Addressed multiple linting and type-mismatch errors across the entire Python stack.
- **Search Resiliency**: Improved fallback mechanisms when Spotify API is disconnected.
- **CSV/Parquet Sync**: Fixed memory leaks and duplicate record creation during heavy synchronization.

---

## [2026-02-20] - Audio Player Evolution & Dynamic Queue
### Added
- **Dynamic Queue System**: Introduced a robust queue management system in Pinia with Shuffle/Loop support.
- **Queue UI**: Added a sleek, blurred "Cola de Reproducción" overlay in the player.
- **Advanced Track Actions**: "Reproducir a continuación" (Play Next) and "Añadir a la cola" (Add to Queue) features.

---

## [Initial Phases] - Project Foundation
- **Core Architecture**: Vue 3 (Composition API) + Pinia + FastAPI + Spotify API.
- **Audio Analysis Engine**: Hybrid recommendation system using content-based local matching ("Vibe").
- **Database Layer**: Parquet/CSV optimized storage for massive user libraries.
- **Premium Design**: Dark-mode primary UI with custom CSS-based animations and layout.

