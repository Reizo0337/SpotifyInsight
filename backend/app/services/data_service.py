
import pandas as pd
import os

BASE_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed")
LIBRARY_PATH = os.path.join(BASE_DATA_DIR, "saved_tracks.csv")
USER_TRACKS_PATH = os.path.join(BASE_DATA_DIR, "user_tracks.csv")

class DataService:
    COLUMNS_ORDER = [
        "spotify_id", "track_name", "artist", "artist_id", "album", "popularity", "genre",
        "danceability", "energy", "tempo", "valence", "acousticness", 
        "instrumentalness", "speechiness", "loudness", "key", "mode"
    ]
    
    _library_cache = None
    _library_mtime = 0

    @staticmethod
    def load_library():
        """Loads all unique tracks with their audio features (with memory caching)."""
        if not os.path.exists(LIBRARY_PATH):
            return pd.DataFrame(columns=DataService.COLUMNS_ORDER)
        
        try:
            # Check if cache is fresh
            current_mtime = os.path.getmtime(LIBRARY_PATH)
            if DataService._library_cache is not None and current_mtime <= DataService._library_mtime:
                return DataService._library_cache

            print(f"Loading library from disk ({round(os.path.getsize(LIBRARY_PATH)/1024/1024, 2)} MB)...")
            df = pd.read_csv(LIBRARY_PATH)
            
            # Map legacy names if they appear
            df = df.rename(columns={
                "Track/Item Name": "track_name",
                "Artist/Detail": "artist"
            })
            
            # Ensure all columns exist and are in the correct order
            for col in DataService.COLUMNS_ORDER:
                if col not in df.columns:
                    if col in ["danceability", "energy", "tempo", "valence", "acousticness", 
                              "instrumentalness", "speechiness", "loudness", "popularity", "key", "mode"]:
                        df[col] = 0.0
                    else:
                        df[col] = "Unknown"
            
            # Reorder
            df = df[DataService.COLUMNS_ORDER]

            # Force numeric types for features to avoid "Unknown" strings in numeric columns
            numeric_cols = [
                "danceability", "energy", "tempo", "valence", 
                "acousticness", "instrumentalness", "speechiness", "loudness",
                "popularity", "key", "mode"
            ]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            # Update cache
            DataService._library_cache = df
            DataService._library_mtime = current_mtime
            
            return df
        except Exception as e:
            print(f"Error loading library: {e}")
            return pd.DataFrame()

    @staticmethod
    def load_data(user_id=None):
        """Loads a specific user's tracks joined with library metadata."""
        if not os.path.exists(USER_TRACKS_PATH):
            return pd.DataFrame()
        
        try:
            user_df = pd.read_csv(USER_TRACKS_PATH)
            if user_id:
                # Prioritize user_id if provided
                user_df = user_df[user_df["user_id"] == user_id]
            
            library_df = DataService.load_library()
            if library_df.empty:
                return pd.DataFrame()
            
            # Join user track list with full metadata
            # We drop duplicated track_name from user_df because it exists in library
            if "track_name" in user_df.columns and "track_name" in library_df.columns:
                user_df = user_df.drop(columns=["track_name"])

            return pd.merge(user_df, library_df, on="spotify_id", how="inner")
        except Exception as e:
            print(f"Error loading user data: {e}")
            return pd.DataFrame()

    @staticmethod
    def save_library(df):
        """Saves unique track metadata to library and updates cache."""
        if df.empty:
            return
            
        # Ensure correct order before saving
        df = df[DataService.COLUMNS_ORDER]
        df.drop_duplicates(subset=["spotify_id"]).to_csv(LIBRARY_PATH, index=False)
        
        # Update cache to avoid reload
        DataService._library_cache = df
        DataService._library_mtime = os.path.getmtime(LIBRARY_PATH)

    @staticmethod
    def save_user_tracks(df):
        """Saves user-track associations."""
        df.to_csv(USER_TRACKS_PATH, index=False)

    @staticmethod
    def append_new_tracks(new_tracks, user_name="DefaultUser", user_id="Unknown"):
        """Adds new tracks to both library and user history with batch optimization."""
        library_df = DataService.load_library()
        new_df = pd.DataFrame(new_tracks)
        
        if new_df.empty:
            return library_df
            
        # 1. Update Library efficiently
        # Use a set for O(1) lookups
        existing_ids = set()
        if not library_df.empty:
            existing_ids = set(library_df["spotify_id"].values)
        
        # Identify TRULY new tracks that aren't in our 5M+ library
        truly_new_tracks = new_df[~new_df["spotify_id"].isin(existing_ids)].copy()
        
        if not truly_new_tracks.empty:
            print(f"Found {len(truly_new_tracks)} new tracks to enrich...")
            from .spotify_service import SpotifyService
            sp = SpotifyService()
            
            # Batch enrichment via Spotify API (100 tracks per request)
            enriched_list = []
            new_ids = truly_new_tracks["spotify_id"].tolist()
            
            for i in range(0, len(new_ids), 100):
                batch_ids = new_ids[i:i+100]
                try:
                    af_list = sp.sp.audio_features(batch_ids)
                    for idx, af in enumerate(af_list):
                        original_row = truly_new_tracks.iloc[i + idx].to_dict()
                        if af:
                            # Merge Spotify features
                            features = {
                                "danceability": af.get("danceability", 0),
                                "energy": af.get("energy", 0),
                                "tempo": af.get("tempo", 0),
                                "valence": af.get("valence", 0),
                                "acousticness": af.get("acousticness", 0),
                                "instrumentalness": af.get("instrumentalness", 0),
                                "speechiness": af.get("speechiness", 0),
                                "loudness": af.get("loudness", 0),
                                "key": af.get("key", 0),
                                "mode": af.get("mode", 0)
                            }
                            enriched_list.append({**original_row, **features})
                        else:
                            enriched_list.append(original_row)
                except Exception as e:
                    print(f"Batch enrichment error: {e}")
                    # Keep original rows without features if it fails
                    for j in range(len(batch_ids)):
                        enriched_list.append(truly_new_tracks.iloc[i+j].to_dict())
            
            # Combine with library
            enriched_df = pd.DataFrame(enriched_list)
            # Ensure order
            for col in DataService.COLUMNS_ORDER:
                if col not in enriched_df.columns:
                    enriched_df[col] = 0 if col in ["popularity", "key", "mode"] else "Unknown"
            
            library_df = pd.concat([library_df, enriched_df[DataService.COLUMNS_ORDER]]).drop_duplicates(
                subset=["spotify_id"], keep="last"
            ).reset_index(drop=True)
            
            DataService.save_library(library_df)
        
        # 2. Update User History (FILTERED)
        if os.path.exists(USER_TRACKS_PATH):
            try:
                user_history = pd.read_csv(USER_TRACKS_PATH)
            except Exception:
                user_history = pd.DataFrame(columns=["user_id", "user_name", "spotify_id", "track_name"])
        else:
            user_history = pd.DataFrame(columns=["user_id", "user_name", "spotify_id", "track_name"])
        
        existing_user_tracks = set()
        if not user_history.empty:
            existing_user_tracks = set(zip(user_history["user_id"].astype(str), user_history["spotify_id"].astype(str)))

        new_mappings = []
        for _, row in new_df.iterrows():
            if (str(user_id), str(row["spotify_id"])) not in existing_user_tracks:
                new_mappings.append({
                    "user_id": user_id,
                    "user_name": user_name,
                    "spotify_id": row["spotify_id"],
                    "track_name": row["track_name"]
                })
        
        if new_mappings:
            new_hist_df = pd.DataFrame(new_mappings)
            user_history = pd.concat([user_history, new_hist_df]).reset_index(drop=True)
            DataService.save_user_tracks(user_history)
            print(f"Added {len(new_mappings)} new tracks to history for {user_name}")

        # Return joined view for the specific user (Filtered to avoid huge join)
        # We only return the last 100 for immediate UI feedback to keep it fast
        current_user_history = user_history[user_history["user_id"] == user_id].tail(100)
        return pd.merge(current_user_history, library_df, on="spotify_id", how="inner")

    @staticmethod
    def persist_track(track_data):
        """Saves or updates a single track in the library."""
        library_df = DataService.load_library()
        
        # Ensure correct column naming for the dataframe
        # Many sources might provide track_name instead of just name, etc.
        data_to_save = {
            "spotify_id": track_data.get("spotify_id") or track_data.get("id"),
            "track_name": track_data.get("track_name") or track_data.get("name"),
            "artist": track_data.get("artist"),
            "artist_id": track_data.get("artist_id"),
            "album": track_data.get("album"),
            "popularity": track_data.get("popularity", 0),
            "genre": track_data.get("genre", "Unknown"),
            "danceability": track_data.get("danceability"),
            "energy": track_data.get("energy"),
            "tempo": track_data.get("tempo"),
            "valence": track_data.get("valence"),
            "acousticness": track_data.get("acousticness"),
            "instrumentalness": track_data.get("instrumentalness"),
            "speechiness": track_data.get("speechiness"),
            "loudness": track_data.get("loudness"),
            "key": track_data.get("key"),
            "mode": track_data.get("mode")
        }
        
        if not data_to_save["spotify_id"]:
            return
            
        new_df = pd.DataFrame([data_to_save])[DataService.COLUMNS_ORDER]
        
        if library_df.empty:
            updated_library = new_df
        else:
            updated_library = pd.concat([library_df, new_df]).drop_duplicates(
                subset=["spotify_id"], 
                keep="last"
            ).reset_index(drop=True)
            
        DataService.save_library(updated_library)
        print(f"Track persisted to library: {data_to_save['track_name']}")
