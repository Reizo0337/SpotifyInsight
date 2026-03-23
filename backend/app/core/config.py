import os
from pathlib import Path
from dotenv import load_dotenv

# Load environmental variables
load_dotenv()

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

# Database Settings (MySQL)
# User should ensure MySQL is running and a 'nebulamusic' database exists
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root@localhost/nebulamusic")
SECRET_KEY = os.getenv("SECRET_KEY", "nebula_super_secret_key_2026_vibes")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days sessions

# Settings
BATCH_SIZE = 100
MAX_RECOMMENDATIONS = 50
CACHE_TTL = 3600 # 1 hour
