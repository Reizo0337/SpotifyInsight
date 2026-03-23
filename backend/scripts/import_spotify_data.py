import pandas as pd
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Track, User
import sys
import os
import requests
import time

# Dataset URL from HuggingFace (Direct Parquet link)
DATASET_URL = "https://huggingface.co/datasets/GildasLeDrogoff/spotify-huge-track-analysis-dataset/resolve/main/spotify-huge-audio-features.parquet"
LOCAL_FILE = "spotify_huge_data.parquet"

def download_and_import():
    print("🌌 Nebula Data Injector: Establishing stable link to HuggingFace...")
    
    # Check if pyarrow is installed (needed for parquet)
    try:
        import pyarrow
    except ImportError:
        print("🛑 Missing 'pyarrow' module. Please run: pip install pyarrow")
        return

    if not os.path.exists(LOCAL_FILE):
        print(f"📡 Downloading 4.3GB of cosmic data from {DATASET_URL}...")
        print("⚠️  Warning: This is a massive file. Ensure you have ~5GB of disk space.")
        try:
            with requests.get(DATASET_URL, stream=True) as r:
                r.raise_for_status()
                with open(LOCAL_FILE, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print("📦 Download complete.")
        except Exception as e:
            print(f"🛑 Error downloading signal: {e}")
            return

    print("📊 Opening Parquet archive (optimized for memory)...")
    try:
        # Parquet is columnar, so we can read it directly
        df = pd.read_parquet(LOCAL_FILE)
    except Exception as e:
        print(f"🛑 Error reading Parquet: {e}")
        return

    db = SessionLocal()
    total_added = 0
    
    print(f"🚀 Detected {len(df)} tracks. Starting bulk injection into SQL repository...")
    try:
        # Process in chunks of 100k
        chunk_size = 100000
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size].copy()
            
            # Map columns to Track model
            # Typical Parquet columns for this dataset: 
            # id, name, artists, album_name, duration_ms, popularity, etc.
            mapping = {
                'id': 'spotify_id',
                'name': 'track_name',
                'artists': 'artist',
                'album_name': 'album',
                'duration_ms': 'duration_ms',
                'popularity': 'popularity',
                'danceability': 'danceability',
                'energy': 'energy',
                'tempo': 'tempo',
                'valence': 'valence'
            }
            
            chunk = chunk.rename(columns=mapping)
            # Keep only columns that exist in our Track model
            valid_cols = [c for c in mapping.values() if c in chunk.columns]
            to_insert = chunk[valid_cols].copy()
            
            # Remove existing tracks to avoid UNIQUE constraint violations
            ids = to_insert['spotify_id'].tolist()
            existing = [r[0] for r in db.query(Track.spotify_id).filter(Track.spotify_id.in_(ids)).all()]
            to_insert = to_insert[~to_insert['spotify_id'].isin(existing)]
            
            if not to_insert.empty:
                engine = db.get_bind()
                to_insert.to_sql('tracks', con=engine, if_exists='append', index=False)
                total_added += len(to_insert)
                print(f"✅ Segment {i//chunk_size + 1} stabilized: {total_added} cumulative tracks.")

        print(f"✨ Mission Success: {total_added} new signals indexed in the galactic repository.")
        
    except Exception as e:
        print(f"🛑 Injection crashed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    download_and_import()
