import os
import time
import pandas as pd
import numpy as np
import json
from pathlib import Path
from ..core.config import LIBRARY_PATH, USER_TRACKS_PATH, PLAYLISTS_PATH, FAVORITES_PATH
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
        "last_load": 0
    }

    @classmethod
    def load_library(cls) -> pd.DataFrame:
        if cls._cache["df"] is not None and (time.time() - cls._cache["last_load"] < 5):
            return cls._cache["df"]
            
        if not LIBRARY_PATH.exists():
            df = pd.DataFrame(columns=cls.COLUMNS_ORDER)
            cls.save_library(df)
            return df
            
        try:
            df = pd.read_parquet(LIBRARY_PATH)
            # Ensure all columns exist
            for col in cls.COLUMNS_ORDER:
                if col not in df.columns:
                    df[col] = 0.0 if col in ["danceability", "energy", "tempo", "valence"] else "Unknown"
            
            cls._cache["df"] = df
            cls._cache["last_load"] = time.time()
            return df
        except Exception as e:
            Logger.error("DATA", f"Load library failed: {e}")
            return pd.DataFrame(columns=cls.COLUMNS_ORDER)

    @classmethod
    def save_library(cls, df: pd.DataFrame):
        try:
            df.to_parquet(LIBRARY_PATH, index=False)
            cls._cache["df"] = df
            cls._cache["last_load"] = time.time()
        except Exception as e:
            Logger.error("DATA", f"Save library failed: {e}")

    @classmethod
    def get_indexed_library(cls):
        lib = cls.load_library()
        if lib.empty: return None
        return lib.set_index("spotify_id")

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
            # Filter metadata to only include known columns
            clean_meta = {k: v for k, v in metadata.items() if k in cls.COLUMNS_ORDER}
            new_row.update(clean_meta)
            
            lib_df = pd.concat([lib_df, pd.DataFrame([new_row])]).reset_index(drop=True)
            changed = True
        else:
            changed = False
            for k, v in metadata.items():
                if k in cls.COLUMNS_ORDER:
                    current_val = lib_df.loc[mask, k].iloc[0]
                    if current_val != v:
                        lib_df.loc[mask, k] = v
                        changed = True
        
        if changed:
            cls.save_library(lib_df)

    @classmethod
    def load_user_data(cls, user_id: str) -> pd.DataFrame:
        if not USER_TRACKS_PATH.exists():
            return pd.DataFrame(columns=["user_id", "user_name", "spotify_id", "track_name", "played_at"])
        
        try:
            df = pd.read_csv(USER_TRACKS_PATH)
            return df[df["user_id"] == user_id]
        except Exception as e:
            Logger.error("DATA", f"Error loading user history: {e}")
            return pd.DataFrame(columns=["user_id", "user_name", "spotify_id", "track_name", "played_at"])

    @classmethod
    def add_to_history(cls, user_id: str, track: dict):
        """Adds a track to the user's historical play log."""
        if not track or "spotify_id" not in track: return
        
        new_row = pd.DataFrame([{
            "user_id": user_id,
            "user_name": "local_user",
            "spotify_id": track["spotify_id"],
            "track_name": track.get("track_name", "Unknown"),
            "played_at": time.time()
        }])
        
        cls._update_history(new_row, user_id, "local_user")

    @staticmethod
    def _update_history(new_df: pd.DataFrame, user_id, user_name):
        """Updates user history CSV, allowing duplicates and adding timestamps."""
        cols = ["user_id", "user_name", "spotify_id", "track_name", "played_at"]
        hist_df = pd.read_csv(USER_TRACKS_PATH) if USER_TRACKS_PATH.exists() else pd.DataFrame(columns=cols)
        
        to_add = new_df.copy()
        to_add["user_id"] = user_id
        to_add["user_name"] = user_name
        
        if "played_at" not in to_add.columns:
            to_add["played_at"] = time.time()
            
        updated = pd.concat([hist_df, to_add[cols]]).reset_index(drop=True)
        updated = updated.tail(5000)
        updated.to_csv(USER_TRACKS_PATH, index=False)

    @staticmethod
    def load_playlists() -> list:
        if not PLAYLISTS_PATH.exists(): return []
        try:
            with open(PLAYLISTS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            Logger.error("DATA", f"Load playlists failed: {e}")
            return []

    @staticmethod
    def save_playlists(playlists: list):
        try:
            with open(PLAYLISTS_PATH, 'w', encoding='utf-8') as f:
                json.dump(playlists, f, ensure_ascii=False, indent=2)
        except Exception as e:
            Logger.error("DATA", f"Save playlists failed: {e}")

    @classmethod
    def create_playlist(cls, name: str, is_public: bool = True):
        import uuid
        playlists = cls.load_playlists()
        new_pl = {
            "id": str(uuid.uuid4()),
            "name": name,
            "is_public": is_public,
            "tracks": [],
            "created_at": time.time()
        }
        playlists.append(new_pl)
        cls.save_playlists(playlists)
        Logger.info("DATA", f"Created playlist: {name} ({new_pl['id']})")
        return new_pl

    @classmethod
    def add_track_to_playlist(cls, playlist_id: str, track_data: dict) -> bool:
        playlists = cls.load_playlists()
        sid = track_data.get("spotify_id")
        if not sid: return False
        
        for pl in playlists:
            if pl["id"] == playlist_id:
                if sid not in pl["tracks"]:
                    pl["tracks"].append(sid)
                    cls.save_playlists(playlists)
                return True
        return False

    @staticmethod
    def load_favorites() -> list:
        if not FAVORITES_PATH.exists(): return []
        try:
            with open(FAVORITES_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []

    @classmethod
    def logout_user(cls):
        # Clear sensitive cache if needed
        cls._cache["df"] = None
        cls._cache["last_load"] = 0

    @classmethod
    def toggle_favorite(cls, track: dict):
        favs = cls.load_favorites()
        sid = track["spotify_id"]
        
        exists = any(f["spotify_id"] == sid for f in favs)
        if exists:
            favs = [f for f in favs if f["spotify_id"] != sid]
            res = False
        else:
            favs.append(track)
            res = True
            
        with open(FAVORITES_PATH, 'w', encoding='utf-8') as f:
            json.dump(favs, f, ensure_ascii=False, indent=2)
        return res
