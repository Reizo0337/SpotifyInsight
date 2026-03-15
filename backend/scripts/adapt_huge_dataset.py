
import os
import pandas as pd
from datasets import load_dataset
from tqdm import tqdm
import time
from app.services.data_service import DataService

# Dataset name
DATASET_NAME = "GildasLeDrogoff/spotify-huge-track-analysis-dataset"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Removed local LIBRARY_PATH to use DataService.LIBRARY_PATH

def adapt_dataset():
    print(f"Loading dataset: {DATASET_NAME}...")
    
    try:
        # Initializing dataset
        dataset = load_dataset(DATASET_NAME, split="train", streaming=True)
        
        # Load existing library to avoid duplicates efficiently
        if os.path.exists(LIBRARY_PATH):
            # We use DataService to ensure we load it correctly
            existing_df = DataService.load_library()
            existing_ids = set(existing_df["spotify_id"].dropna().unique())
            print(f"Loaded existing library with {len(existing_ids)} tracks.")
        else:
            existing_ids = set()
            print("No existing library found. Creating new one.")

        # Fields mapping (Source -> Our Format)
        mapping = {
            "track_id": "spotify_id",
            "artist_name": "artist",
            "track_name": "track_name",
            "album_name": "album",
            "track_popularity": "popularity",
            "tempo": "tempo",
            "key": "key",
            "mode": "mode",
            "danceability": "danceability",
            "energy": "energy",
            "loudness": "loudness",
            "speechiness": "speechiness",
            "acousticness": "acousticness",
            "instrumentalness": "instrumentalness",
            "valence": "valence"
        }

        batch = []
        batch_size = 50000 
        processed_count = 0
        added_count = 0
        max_tracks = 5000000 
        
        print(f"Synchronizing up to {max_tracks} tracks...")
        
        start_time = time.time()
        
        for row in tqdm(dataset):
            processed_count += 1
            
            sid = row.get("track_id")
            if not sid or sid in existing_ids:
                continue
                
            # Adapt row
            mapped_row = {}
            for src, target in mapping.items():
                mapped_row[target] = row.get(src)
            
            # Additional defaults for fields not in this dataset
            mapped_row["genre"] = "Unknown"
            mapped_row["artist_id"] = "Unknown"
            
            # Ensure all columns from COLUMNS_ORDER are present
            for col in DataService.COLUMNS_ORDER:
                if col not in mapped_row:
                    mapped_row[col] = 0.0 if col in ["popularity", "key", "mode"] else "Unknown"

            batch.append(mapped_row)
            existing_ids.add(sid)
            added_count += 1
            
            if len(batch) >= batch_size:
                save_batch(batch)
                batch = []
                print(f" - Saved batch. Total added: {added_count}")
            
            if added_count >= max_tracks:
                break

        if batch:
            save_batch(batch)
            
        end_time = time.time()
        print(f"\nDone! Processed {processed_count} tracks.")
        print(f"Added {added_count} new tracks to library.")
        print(f"Total library size: {len(DataService.load_library())}")
        print(f"Time taken: {round(end_time - start_time, 2)} seconds.")

    except Exception as e:
        print(f"Error during adaptation: {e}")
        import traceback
        traceback.print_exc()

def save_batch(batch):
    import time
    t_start = time.time()
    # Use DataService order and save method (handles Parquet + Cache)
    df_new = pd.DataFrame(batch)[DataService.COLUMNS_ORDER]
    
    current_lib = DataService.load_library()
    updated_lib = pd.concat([current_lib, df_new]).drop_duplicates(subset=["spotify_id"])
    DataService.save_library(updated_lib)
    print(f"[ADAPT] Batch saved in {time.time()-t_start:.3f}s")

if __name__ == "__main__":
    adapt_dataset()
