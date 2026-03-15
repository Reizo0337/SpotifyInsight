# 🎵 Spotify Wrapped Rework - Backend

Welcome to the backend engine of **Spotify Wrapped Rework**, a sophisticated music analysis and recommendation platform focused on local digital signal processing (DSP).

## 🚀 Key Features

- **Hybrid Audio Engine**: Combines official Spotify metadata with local audio analysis.
- **DSP DNA Extraction**: Calculates Tempo, Energy, Danceability, and more directly from audio previews.
- **Circuit Breaker System**: Automatic protection against Spotify API 403 restrictions.
- **Ultra-Fast Recommendations**: Vectorized similarity engine (NumPy/Sklearn) for O(1) matching.
- **Big Data Ready**: Powered by Parquet columnar storage supporting millions of tracks.

## 📖 Documentation

For a deep dive into the architecture, services, and API, please refer to the:
👉 **[Full Project Documentation](DOCUMENTATION.md)**

## 🛠 Quick Start

### 1. Requirements
Ensure you have Python 3.10+ and FFmpeg installed on your system.

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Environment Config
Create a `.env` file in the root directory:
```env
SPOTIPY_CLIENT_ID=your_id
SPOTIPY_CLIENT_SECRET=your_secret
```

### 4. Run the API
```bash
python run.py
```

## 📡 API Overview

- `GET /api/sync`: Modernized high-speed synchronization.
- `GET /api/recommendations`: Hybrid local/remote engine.
- `GET /api/stats`: Insights into your musical library.
- `GET /api/analyze-track`: Deep dive into any specific song.

---
*Built with passion by Antigravity AI Engineering - 2026*
