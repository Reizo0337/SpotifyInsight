import os
import time
import pandas as pd
import numpy as np
from ..core.config import LIBRARY_PATH, USER_TRACKS_PATH
from ..core.logging import Logger

class DataService:
    COLUMNS_ORDER = [
        "spotify_id", "track_name", "artist", "artist_id", "album", "popularity", "genre",
        "thumbnail", "duration_ms",
        "danceability", "energy", "tempo", "valence", "acousticness", 
        "instrumentalness", "speechiness", "loudness", "key", "mode", "yt_id",
        "stream_url", "stream_expiry"
    ]
    
    _cache = {
        "df": None,
        "mtime": 0,
        "ids": set(),
        "indexed": pd.DataFrame()
    }

    @classmethod
    def load_library(cls) -> pd.DataFrame:
        """Loads the music library with memory caching and Parquet optimization."""
        if not LIBRARY_PATH.exists():
            empty_df = pd.DataFrame(columns=cls.COLUMNS_ORDER)
            cls._cache.update({"ids": set(), "indexed": empty_df.set_index("spotify_id")})
            return empty_df
        
        try:
            mtime = os.path.getmtime(LIBRARY_PATH)
            if cls._cache["df"] is not None and mtime <= cls._cache["mtime"]:
                return cls._cache["df"]

            start_time = time.time()
            df = pd.read_parquet(LIBRARY_PATH)
            df = cls._sanitize_df(df)
            
            cls._cache.update({
                "df": df,
                "mtime": mtime,
                "ids": set(df["spotify_id"].values),
                "indexed": df[df["energy"] > 0].set_index("spotify_id")
            })
            
            Logger.time("DATA", "Library loaded and indexed", start_time)
            return df
        except Exception as e:
            Logger.error("DATA", f"Load library failed: {e}")
            return pd.DataFrame(columns=cls.COLUMNS_ORDER)

    @classmethod
    def get_indexed_library(cls) -> pd.DataFrame:
        """Returns the indexed cache for O(1) lookups."""
        cls.load_library()
        return cls._cache["indexed"]

    @classmethod
    def _sanitize_df(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Ensures consistent columns and types using vectorized operations."""
        # Add missing columns
        missing = set(cls.COLUMNS_ORDER) - set(df.columns)
        for col in missing:
            if col in ["danceability", "energy", "tempo", "valence", "acousticness", 
                       "instrumentalness", "speechiness", "loudness", "popularity", "key", "mode", "stream_expiry", "duration_ms"]:
                df[col] = 0.0
            elif col == "thumbnail":
                df[col] = None
            else:
                df[col] = "Unknown"
        
        # Repair accidental "Unknown" values from previous bug
        if "thumbnail" in df.columns:
            df["thumbnail"] = df["thumbnail"].replace("Unknown", None)
        if "duration_ms" in df.columns:
            # Aggressive fix: convert to numeric, making errors (like "Unknown") NaN then 0
            df["duration_ms"] = pd.to_numeric(df["duration_ms"], errors='coerce').fillna(0).astype('int32')
        
        # Cast types efficiently
        numeric_cols = ["danceability", "energy", "tempo", "valence", "acousticness", 
                       "instrumentalness", "speechiness", "loudness"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0.0).astype('float32')
        
        int_cols = ["popularity", "key", "mode", "duration_ms"]
        df[int_cols] = df[int_cols].apply(pd.to_numeric, errors='coerce').fillna(0).astype('int32')
            
        return df[cls.COLUMNS_ORDER]

    @classmethod
    def save_library(cls, df: pd.DataFrame):
        """Saves library to Parquet and invalidates cache."""
        if df.empty: return
        t_start = time.time()
        df = cls._sanitize_df(df).drop_duplicates(subset=["spotify_id"])
        df.to_parquet(LIBRARY_PATH, index=False)
        cls._cache["mtime"] = 0 
        Logger.time("DATA", "Library saved", t_start)

    @staticmethod
    def load_user_data(user_id=None) -> pd.DataFrame:
        """Loads user history joined with features using efficient filtering."""
        if not USER_TRACKS_PATH.exists(): return pd.DataFrame()
        
        try:
            t_start = time.time()
            user_df = pd.read_csv(USER_TRACKS_PATH)
            if user_id:
                user_df = user_df[user_df["user_id"].astype(str) == str(user_id)]
            
            lib_df = DataService.load_library()
            if lib_df.empty or user_df.empty: return pd.DataFrame()
            
            # Efficient join on unique IDs
            relevant_ids = user_df["spotify_id"].unique()
            filtered_lib = lib_df[lib_df["spotify_id"].isin(relevant_ids)]
            
            # Clean columns to avoid duplication
            user_df_clean = user_df.drop(columns=[c for c in ["track_name", "artist", "album"] if c in user_df.columns])
            res = pd.merge(user_df_clean, filtered_lib, on="spotify_id", how="inner")
            
            Logger.time("DATA", f"User history loaded ({len(res)} rows)", t_start)
            return res
        except Exception as e:
            Logger.error("DATA", f"Load user data failed: {e}")
            return pd.DataFrame()

    @classmethod
    def append_new_tracks(cls, new_tracks: list, user_name="DefaultUser", user_id="Unknown"):
        """High-performance sync for new tracks."""
        t_start = time.time()
        cls.load_library()
        new_df = pd.DataFrame(new_tracks)
        if new_df.empty: return pd.DataFrame()
        
        # Detect truly new items
        new_df["spotify_id"] = new_df["spotify_id"].astype(str)
        mask = ~new_df["spotify_id"].isin(cls._cache["ids"])
        truly_new_tracks = new_df[mask].copy()
        
        if not truly_new_tracks.empty:
            cls._enrich_and_save(truly_new_tracks)
        
        # Metadata check for existing tracks
        remaining_mask = new_df["spotify_id"].isin(cls._cache["ids"])
        existing_updates = new_df[remaining_mask]
        
        if not existing_updates.empty:
            lib_df = cls.load_library()
            updated = False
            for _, row in existing_updates.iterrows():
                sid = row["spotify_id"]
                idx_mask = lib_df["spotify_id"] == sid
                if idx_mask.any():
                    existing_row = lib_df.loc[idx_mask].iloc[0]
                    if (existing_row.get("thumbnail") in [None, "Unknown", ""]) and row.get("thumbnail"):
                        lib_df.loc[idx_mask, "thumbnail"] = row["thumbnail"]
                        updated = True
                    if (existing_row.get("duration_ms", 0) == 0) and row.get("duration_ms", 0) > 0:
                        lib_df.loc[idx_mask, "duration_ms"] = row["duration_ms"]
                        updated = True
                    if (existing_row.get("popularity", 0) == 0) and row.get("popularity", 0) > 0:
                        lib_df.loc[idx_mask, "popularity"] = int(row["popularity"])
                        updated = True
                    if (existing_row.get("genre") == "Unknown") and row.get("genre") != "Unknown":
                        lib_df.loc[idx_mask, "genre"] = row["genre"]
                        updated = True
            
            if updated:
                cls.save_library(lib_df)
        
        cls._update_history(new_df, user_id, user_name)
        
        Logger.time("DATA", "Append tracks completed", t_start)
        return cls.load_user_data(user_id).tail(100)

    @classmethod
    def log_track_play(cls, track_metadata: dict, user_id="Unknown", user_name="DefaultUser"):
        """Logs a single track play event with full metadata enrichment."""
        cls.append_new_tracks([track_metadata], user_name=user_name, user_id=user_id)

    @classmethod
    def update_track_metadata(cls, spotify_id: str, metadata: dict, track_name: str = "Unknown", artist: str = "Unknown"):
        """Updates or CREATES track metadata efficiently."""
        if not spotify_id: return
        
        lib_df = cls.load_library()
        mask = lib_df["spotify_id"] == spotify_id
        
        if not mask.any():
            # Create new row
            new_row = {col: 0.0 if col in ["danceability", "energy", "tempo", "valence", "acousticness", 
                       "instrumentalness", "speechiness", "loudness", "popularity", "key", "mode", "stream_expiry"] else "Unknown" 
                       for col in cls.COLUMNS_ORDER}
            new_row.update({"spotify_id": spotify_id, "track_name": track_name, "artist": artist})
            new_row.update(metadata)
            lib_df = pd.concat([lib_df, pd.DataFrame([new_row])]).reset_index(drop=True)
            changed = True
        else:
            changed = False
            for k, v in metadata.items():
                if k in cls.COLUMNS_ORDER and lib_df.loc[mask, k].iloc[0] != v:
                    lib_df.loc[mask, k] = v
                    changed = True
        
        if changed:
            cls.save_library(lib_df)
            # Incremental CSV sync
            try:
                lib_df.to_csv(LIBRARY_PATH.with_suffix(".csv"), index=False)
            except: pass

    @classmethod
    def _enrich_and_save(cls, tracks_df: pd.DataFrame):
        from .spotify_service import SpotifyService
        from .audio_analysis_service import AudioAnalysisService
        sp = SpotifyService()
        
        enriched = []
        can_use_sp = "audio_features" not in sp._forbidden_endpoints
        
        for i in range(0, len(tracks_df), 100):
            batch_df = tracks_df.iloc[i:i+100]
            batch_ids = batch_df["spotify_id"].tolist()
            
            features = {}
            if can_use_sp:
                sp_f = sp.get_audio_features(batch_ids)
                features = {batch_ids[j]: f for j, f in enumerate(sp_f) if f}
                if "audio_features" in sp._forbidden_endpoints: can_use_sp = False
            
            for _, row in batch_df.iterrows():
                sid = row["spotify_id"]
                track_data = row.to_dict()
                
                if sid not in features:
                    Logger.info("DATA", f"Analyzing locally: {row['track_name']}")
                    preview = AudioAnalysisService.get_preview_from_itunes(row["track_name"], row["artist"])
                    local_f = AudioAnalysisService.analyze_preview(preview)
                    if local_f: features[sid] = local_f
                
                if sid in features:
                    track_data.update({k: features[sid].get(k, 0) for k in cls.COLUMNS_ORDER if k in features[sid]})
                
                enriched.append(track_data)
            
        lib = cls.load_library()
        final_lib = pd.concat([lib, pd.DataFrame(enriched)]).drop_duplicates(subset=["spotify_id"], keep="last")
        cls.save_library(final_lib)

    @staticmethod
    def _update_history(new_df: pd.DataFrame, user_id, user_name):
        """Updates user history CSV, allowing duplicates and adding timestamps."""
        cols = ["user_id", "user_name", "spotify_id", "track_name", "played_at"]
        hist_df = pd.read_csv(USER_TRACKS_PATH) if USER_TRACKS_PATH.exists() else pd.DataFrame(columns=cols)
        
        # Ensure played_at exists in historical data
        if "played_at" not in hist_df.columns:
            hist_df["played_at"] = time.time()
        
        to_add = new_df.copy()
        to_add["user_id"] = user_id
        to_add["user_name"] = user_name
        
        if "played_at" not in to_add.columns:
            to_add["played_at"] = time.time()
            
        # Ensure all required columns exist in the dataframe to add
        for col in cols:
            if col not in to_add.columns:
                to_add[col] = "Unknown"
            
        updated = pd.concat([hist_df, to_add[cols]]).reset_index(drop=True)
        # Limit history to last 5000 tracks to avoid massive CSVs
        updated = updated.tail(5000)
        updated.to_csv(USER_TRACKS_PATH, index=False)
