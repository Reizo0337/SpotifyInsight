
import pandas as pd
import os

BASE_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed")
LIBRARY_PATH = os.path.join(BASE_DATA_DIR, "saved_tracks.csv")
USER_TRACKS_PATH = os.path.join(BASE_DATA_DIR, "user_tracks.csv")

class DataService:
    @staticmethod
    def load_library():
        """Loads all unique tracks with their audio features."""
        if not os.path.exists(LIBRARY_PATH):
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(LIBRARY_PATH)
            
            # Map legacy names if they appear
            df = df.rename(columns={
                "Track/Item Name": "track_name",
                "Artist/Detail": "artist"
            })
            
            # Ensure proper types for audio features
            float_features = [
                "danceability", "energy", "tempo", "valence", 
                "acousticness", "instrumentalness", "speechiness", "loudness"
            ]
            for col in float_features:
                if col not in df.columns:
                    df[col] = 0.0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
            
            # Ensure other required columns
            for col in ["popularity", "spotify_id", "artist_id", "genre", "key", "mode"]:
                if col not in df.columns:
                    df[col] = 0 if col in ["popularity", "key", "mode"] else "Unknown"
            
            return df
        except Exception as e:
            print(f"Error loading library: {e}")
            return pd.DataFrame()

    @staticmethod
    def load_data(user_name="DefaultUser"):
        """Loads a specific user's tracks joined with library metadata."""
        if not os.path.exists(USER_TRACKS_PATH):
            return pd.DataFrame()
        
        try:
            user_df = pd.read_csv(USER_TRACKS_PATH)
            user_df = user_df[user_df["user_name"] == user_name]
            
            library_df = DataService.load_library()
            if library_df.empty:
                return pd.DataFrame()
            
            # Join user track list with full metadata
            return pd.merge(user_df, library_df, on="spotify_id", how="inner")
        except Exception as e:
            print(f"Error loading user data: {e}")
            return pd.DataFrame()

    @staticmethod
    def save_library(df):
        """Saves unique track metadata to library."""
        df.drop_duplicates(subset=["spotify_id"]).to_csv(LIBRARY_PATH, index=False)

    @staticmethod
    def save_user_tracks(df):
        """Saves user-track associations."""
        df.to_csv(USER_TRACKS_PATH, index=False)

    @staticmethod
    def append_new_tracks(new_tracks, user_name="DefaultUser"):
        """Adds new tracks to both library and user history, then heals missing features."""
        library_df = DataService.load_library()
        new_df = pd.DataFrame(new_tracks)
        
        # 1. Update Library (Universal metadata)
        if library_df.empty:
            updated_library = new_df
        else:
            updated_library = pd.concat([library_df, new_df]).drop_duplicates(
                subset=["spotify_id"], 
                keep="last"
            ).reset_index(drop=True)
        
        # 2. Update User History
        user_history = pd.read_csv(USER_TRACKS_PATH) if os.path.exists(USER_TRACKS_PATH) else pd.DataFrame(columns=["user_name", "spotify_id"])
        
        new_user_mappings = pd.DataFrame({
            "user_name": [user_name] * len(new_df),
            "spotify_id": new_df["spotify_id"]
        })
        
        updated_user_history = pd.concat([user_history, new_user_mappings]).drop_duplicates(
            subset=["user_name", "spotify_id"],
            keep="last"
        ).reset_index(drop=True)
        
        # 3. Heal Library (only analysis needed for tracks with 0s)
        from .audio_analysis_service import AudioAnalysisService
        from .spotify_service import SpotifyService
        
        # We search FOR ALL tracks in library that need fixing, in case some were added before
        mask_to_analyze = (updated_library["energy"] == 0) | (updated_library["danceability"] == 0)
        # We only fix tracks that actually exist in the library dataset
        to_analyze = updated_library[mask_to_analyze].head(20)
        
        if not to_analyze.empty:
            print(f"Analyzing {len(to_analyze)} tracks in library...")
            sp = SpotifyService()
            for idx, row in to_analyze.iterrows():
                # Avoid re-analyzing if we already have it in a separate check (metadata might have been updated)
                # but here 'idx' is correct for 'updated_library'
                
                # 1. Try Spotify Official Features first
                features = None
                try:
                    af = sp.sp.audio_features([row["spotify_id"]])
                    if af and af[0]:
                        features = {
                            "danceability": af[0].get("danceability"),
                            "energy": af[0].get("energy"),
                            "tempo": af[0].get("tempo"),
                            "valence": af[0].get("valence"),
                            "acousticness": af[0].get("acousticness"),
                            "instrumentalness": af[0].get("instrumentalness"),
                            "speechiness": af[0].get("speechiness"),
                            "loudness": af[0].get("loudness"),
                            "key": af[0].get("key"),
                            "mode": af[0].get("mode")
                        }
                except Exception:
                    pass

                # 2. Fallback to Local Analysis
                if not features:
                    track_info = sp.sp.track(row["spotify_id"])
                    preview_url = track_info.get("preview_url")
                    
                    if not preview_url:
                        preview_url = AudioAnalysisService.get_preview_from_itunes(row["track_name"], row["artist"])
                    
                    if preview_url:
                        features = AudioAnalysisService.analyze_preview(preview_url)
                
                if features:
                    for key, val in features.items():
                        if key in updated_library.columns:
                            updated_library.at[idx, key] = val
        
        # Final Saves
        DataService.save_library(updated_library)
        DataService.save_user_tracks(updated_user_history)
        
        # Return the joined view for the frontend
        return pd.merge(updated_user_history[updated_user_history["user_name"] == user_name], updated_library, on="spotify_id", how="inner")

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
            
        new_df = pd.DataFrame([data_to_save])
        
        if library_df.empty:
            updated_library = new_df
        else:
            updated_library = pd.concat([library_df, new_df]).drop_duplicates(
                subset=["spotify_id"], 
                keep="last"
            ).reset_index(drop=True)
            
        DataService.save_library(updated_library)
        print(f"Track persisted to library: {data_to_save['track_name']}")
