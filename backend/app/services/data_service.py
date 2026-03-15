import os
import time
import pandas as pd
from ..core.config import LIBRARY_PATH, USER_TRACKS_PATH
from ..core.logging import Logger

class DataService:
    COLUMNS_ORDER = [
        "spotify_id", "track_name", "artist", "artist_id", "album", "popularity", "genre",
        "danceability", "energy", "tempo", "valence", "acousticness", 
        "instrumentalness", "speechiness", "loudness", "key", "mode"
    ]
    
    _cache = {
        "df": None,
        "mtime": 0,
        "ids": set(),
        "indexed": pd.DataFrame()
    }

    @classmethod
    def load_library(cls):
        """Loads the music library with memory caching and Parquet optimization."""
        if not LIBRARY_PATH.exists():
            # Return empty but ensure cache is initialized format
            empty_df = pd.DataFrame(columns=cls.COLUMNS_ORDER)
            cls._cache["ids"] = set()
            cls._cache["indexed"] = empty_df.set_index("spotify_id") if "spotify_id" in empty_df.columns else pd.DataFrame()
            return empty_df
        
        try:
            mtime = os.path.getmtime(LIBRARY_PATH)
            if cls._cache["df"] is not None and mtime <= cls._cache["mtime"]:
                return cls._cache["df"]

            start_time = time.time()
            df = pd.read_parquet(LIBRARY_PATH)
            
            # Data Integrity
            df = cls._sanitize_df(df)
            
            # Update Cache
            cls._cache.update({
                "df": df,
                "mtime": mtime,
                "ids": set(df["spotify_id"].astype(str)),
                "indexed": df[df["energy"] != 0].set_index("spotify_id")
            })
            
            Logger.time("DATA", "Library loaded and indexed", start_time)
            return df
        except Exception as e:
            Logger.error("DATA", f"Load library failed: {e}")
            return pd.DataFrame(columns=cls.COLUMNS_ORDER)

    @classmethod
    def get_indexed_library(cls):
        """Returns the indexed cache for O(1) lookups."""
        cls.load_library()
        return cls._cache["indexed"]

    @classmethod
    def _sanitize_df(cls, df):
        """Ensures consistent columns and types."""
        # Ensure all columns exist
        for col in cls.COLUMNS_ORDER:
            if col not in df.columns:
                df[col] = 0.0 if col in ["danceability", "energy", "tempo", "valence", "acousticness", 
                                      "instrumentalness", "speechiness", "loudness", "popularity", "key", "mode"] else "Unknown"
        
        numeric_cols = ["danceability", "energy", "tempo", "valence", "acousticness", 
                       "instrumentalness", "speechiness", "loudness"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype('float32')
        
        int_cols = ["popularity", "key", "mode"]
        for col in int_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int32')
            
        return df[cls.COLUMNS_ORDER]

    @classmethod
    def save_library(cls, df):
        """Saves library to Parquet and invalidates cache."""
        if df.empty: return
        t_start = time.time()
        df = cls._sanitize_df(df).drop_duplicates(subset=["spotify_id"])
        df.to_parquet(LIBRARY_PATH, index=False)
        cls._cache["mtime"] = 0 # Force reload
        Logger.time("DATA", "Library saved", t_start)

    @staticmethod
    def load_user_data(user_id=None):
        """Loads user history joined with features."""
        if not USER_TRACKS_PATH.exists(): return pd.DataFrame()
        
        try:
            t_start = time.time()
            user_df = pd.read_csv(USER_TRACKS_PATH)
            if user_id:
                user_df = user_df[user_df["user_id"].astype(str) == str(user_id)]
            
            lib_df = DataService.load_library()
            if lib_df.empty: return pd.DataFrame()
            
            # Efficient join
            relevant_ids = user_df["spotify_id"].unique()
            filtered_lib = lib_df[lib_df["spotify_id"].isin(relevant_ids)]
            # Drop columns from user_df that are also in lib_df (except the join key)
            user_df_clean = user_df.drop(columns=[c for c in ["track_name", "artist", "album"] if c in user_df.columns])
            res = pd.merge(user_df_clean, filtered_lib, on="spotify_id", how="inner")
            
            Logger.time("DATA", f"User history loaded ({len(res)} rows)", t_start)
            return res
        except Exception as e:
            Logger.error("DATA", f"Load user data failed: {e}")
            return pd.DataFrame()

    @classmethod
    def append_new_tracks(cls, new_tracks, user_name="DefaultUser", user_id="Unknown"):
        """High-performance sync for new tracks."""
        t_start = time.time()
        cls.load_library()
        new_df = pd.DataFrame(new_tracks)
        if new_df.empty: return pd.DataFrame()
        
        # 1. New Tracks Detection (O(1) lookups)
        truly_new_ids = [sid for sid in new_df["spotify_id"].astype(str) if sid not in cls._cache["ids"]]
        truly_new_tracks = new_df[new_df["spotify_id"].astype(str).isin(truly_new_ids)].copy()
        
        if not truly_new_tracks.empty:
            cls._enrich_and_save(truly_new_tracks)
        
        # 2. History update
        cls._update_history(new_df, user_id, user_name)
        
        # 3. Quick result for UI
        res = cls.load_user_data(user_id).tail(100)
        Logger.time("DATA", "Append tracks completed", t_start)
        return res

    @classmethod
    def _enrich_and_save(cls, tracks_df):
        from .spotify_service import SpotifyService
        from .audio_analysis_service import AudioAnalysisService
        sp = SpotifyService()
        
        ids = tracks_df["spotify_id"].tolist()
        enriched = []
        
        # Check if we can use Spotify Features
        can_use_spotify = "audio_features" not in SpotifyService._forbidden_endpoints
        
        for i in range(0, len(ids), 100):
            batch_df = tracks_df.iloc[i:i+100]
            batch_ids = batch_df["spotify_id"].tolist()
            
            features_dict = {}
            if can_use_spotify:
                sp_features = sp.get_audio_features(batch_ids)
                for idx, f in enumerate(sp_features):
                    if f: features_dict[batch_ids[idx]] = f
                
                if "audio_features" in SpotifyService._forbidden_endpoints:
                    can_use_spotify = False
            
            # Fallback to local analysis for missing features
            for idx, row in batch_df.iterrows():
                sid = row["spotify_id"]
                track_data = row.to_dict()
                
                if sid not in features_dict:
                    # LOCAL ANALYSIS FALLBACK
                    Logger.info("DATA", f"Analyzing locally: {row['track_name']} - {row['artist']}")
                    preview_url = AudioAnalysisService.get_preview_from_itunes(row["track_name"], row["artist"])
                    local_f = AudioAnalysisService.analyze_preview(preview_url)
                    if local_f:
                        features_dict[sid] = local_f
                
                if sid in features_dict:
                    track_data.update({k: features_dict[sid].get(k, 0) for k in cls.COLUMNS_ORDER if k in features_dict[sid]})
                
                enriched.append(track_data)
            
        lib_df = cls.load_library()
        new_lib = pd.concat([lib_df, pd.DataFrame(enriched)]).drop_duplicates(subset=["spotify_id"], keep="last")
        cls.save_library(new_lib)

    @staticmethod
    def _update_history(new_df, user_id, user_name):
        hist_df = pd.read_csv(USER_TRACKS_PATH) if USER_TRACKS_PATH.exists() else pd.DataFrame(columns=["user_id", "user_name", "spotify_id", "track_name"])
        
        uid = str(user_id)
        current_user_ids = set(hist_df[hist_df["user_id"].astype(str) == uid]["spotify_id"].astype(str))
        
        new_rows = []
        for _, row in new_df.iterrows():
            if str(row["spotify_id"]) not in current_user_ids:
                new_rows.append({
                    "user_id": user_id,
                    "user_name": user_name,
                    "spotify_id": row["spotify_id"],
                    "track_name": row["track_name"]
                })
        
        if new_rows:
            updated_hist = pd.concat([hist_df, pd.DataFrame(new_rows)]).reset_index(drop=True)
            updated_hist.to_csv(USER_TRACKS_PATH, index=False)
