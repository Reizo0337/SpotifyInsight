import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

# File Paths
LIBRARY_PATH = DATA_DIR / "saved_tracks.parquet"
USER_TRACKS_PATH = DATA_DIR / "user_tracks.csv"
PLAYLISTS_PATH = DATA_DIR / "playlists.json"
FAVORITES_PATH = DATA_DIR / "favorites.json"

# Create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Settings
BATCH_SIZE = 100
MAX_RECOMMENDATIONS = 50
CACHE_TTL = 3600 # 1 hour
