import time
import requests
from ..core.spotify_auth import get_spotify_client
from ..core.logging import Logger

class SpotifyService:
    _forbidden_endpoints = set()
    _last_429_time = 0
    _429_COOLDOWN = 60 # Seconds to stay frozen after a 429

    def __init__(self):
        self.sp = None
        self.user_name = "Guest"
        self.user_id = "local_user"
        
        # Immediate return if we are in global cooldown
        if "ALL" in self._forbidden_endpoints:
            if time.time() - self._last_429_time < self._429_COOLDOWN:
                return
            else:
                self._forbidden_endpoints.remove("ALL")

        try:
            # We try to get the client but we NEVER make a network call here
            self.sp = get_spotify_client()
            if self.sp:
                # Fetch user profile immediately
                user = self._call_api("me")
                if user:
                    self.user_name = user.get("display_name", "Spotify User")
                    self.user_id = user.get("id", "local_user")
        except Exception as e:
            Logger.warning("SPOTIFY", f"Auth client failed: {e}")
            self.sp = None

    def is_connected(self):
        # We consider it "connected" only if we have a client AND we aren't in cooldown
        return self.sp is not None and "ALL" not in self._forbidden_endpoints

    def get_user_profile(self):
        return {"user_name": self.user_name, "user_id": self.user_id}

    def _call_api(self, method_name, *args, **kwargs):
        """Wrapper for API calls with circuit breaker."""
        if not self.sp or "ALL" in self._forbidden_endpoints or method_name in self._forbidden_endpoints:
            return None
            
        try:
            func = getattr(self.sp, method_name)
            return func(*args, **kwargs)
        except Exception as e:
            msg = str(e).lower()
            if "403" in msg or "forbidden" in msg:
                Logger.error("SPOTIFY", f"Forbidden on {method_name}. Disabling.")
                self._forbidden_endpoints.add(method_name)
            elif "429" in msg or "rate limit" in msg:
                Logger.warning("SPOTIFY", f"Rate Limit (429) - Freezing Spotify for {self._429_COOLDOWN}s")
                self._forbidden_endpoints.add("ALL")
                self._last_429_time = time.time()
            else:
                Logger.error("SPOTIFY", f"API Error on {method_name}: {e}")
            return None

    def get_audio_features(self, track_ids):
        res = self._call_api("audio_features", track_ids)
        return res if res else [None] * len(track_ids)

    def get_artists(self, artist_ids):
        all_artists = []
        artist_ids = [aid for aid in artist_ids if aid]
        for i in range(0, len(artist_ids), 50):
            batch = artist_ids[i:i+50]
            res = self._call_api("artists", batch)
            if res and "artists" in res:
                all_artists.extend(res["artists"])
        return all_artists

    def get_tracks(self, track_ids):
        all_tracks = []
        track_ids = [tid for tid in track_ids if tid]
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i+50]
            res = self._call_api("tracks", batch)
            if res and "tracks" in res:
                all_tracks.extend(res["tracks"])
        return all_tracks

    def get_top_tracks_with_features(self, limit=50):
        t_start = time.time()
        if not self.sp: return []
        
        results = self._call_api("current_user_top_tracks", time_range="medium_term", limit=limit)
        if not results or "items" not in results: return []
        
        tracks = results["items"]
        track_ids = [t["id"] for t in tracks]
        
        from .data_service import DataService
        lib_lookup = DataService.get_indexed_library()
        
        final_features = {}
        missing_ids = []
        
        for tid in track_ids:
            if lib_lookup is not None and tid in lib_lookup.index:
                final_features[tid] = lib_lookup.loc[tid].to_dict()
            else:
                missing_ids.append(tid)
        
        if missing_ids:
            af_list = self.get_audio_features(missing_ids)
            for idx, af in enumerate(af_list):
                if af: final_features[missing_ids[idx]] = af

        artist_ids = list(set([t["artists"][0]["id"] for t in tracks if t.get("artists")]))
        artist_genres = {a["id"]: a["genres"][0] for a in self.get_artists(artist_ids) if a and a.get("genres")}
        
        data = [self._map_track(t, final_features.get(t["id"], {}), artist_genres) for t in tracks]
        Logger.time("SPOTIFY", "Top tracks processed", t_start)
        return data

    def get_recently_played_with_features(self, limit=50):
        t_start = time.time()
        if not self.sp: return []
        
        results = self._call_api("current_user_recently_played", limit=limit)
        if not results or "items" not in results: return []
        
        tracks = [item["track"] for item in results["items"] if item.get("track")]
        if not tracks: return []
            
        track_ids = [t["id"] for t in tracks]
        from .data_service import DataService
        lib_lookup = DataService.get_indexed_library()
        
        final_features = {}
        missing_ids = []
        for tid in track_ids:
            if lib_lookup is not None and tid in lib_lookup.index:
                final_features[tid] = lib_lookup.loc[tid].to_dict()
            else:
                missing_ids.append(tid)
        
        if missing_ids:
            af_list = self.get_audio_features(missing_ids)
            for idx, af in enumerate(af_list):
                if af: final_features[missing_ids[idx]] = af
            
        artist_ids = list(set([t["artists"][0]["id"] for t in tracks if t.get("artists")]))
        artist_genres = {a["id"]: a["genres"][0] for a in self.get_artists(artist_ids) if a and a.get("genres")}

        data = [self._map_track(t, final_features.get(t["id"], {}), artist_genres) for t in tracks]
        Logger.time("SPOTIFY", "Recently played processed", t_start)
        return data

    def _map_track(self, track, features, artist_genres):
        main_artist = track["artists"][0] if track.get("artists") else {}
        album = track.get("album", {})
        images = album.get("images", [])
        return {
            "track_name": track.get("name", "Unknown"),
            "artist": main_artist.get("name", "Unknown"),
            "artist_id": main_artist.get("id"),
            "album": album.get("name", "Unknown"),
            "thumbnail": images[0]["url"] if images else None,
            "duration_ms": track.get("duration_ms", 0),
            "popularity": track.get("popularity", 0),
            "genre": artist_genres.get(main_artist.get("id"), "Unknown"),
            "danceability": features.get("danceability", 0),
            "energy": features.get("energy", 0),
            "tempo": features.get("tempo", 0),
            "valence": features.get("valence", 0),
            "acousticness": features.get("acousticness", 0),
            "instrumentalness": features.get("instrumentalness", 0),
            "speechiness": features.get("speechiness", 0),
            "loudness": features.get("loudness", 0),
            "key": features.get("key", 0),
            "mode": features.get("mode", 0),
            "spotify_id": track["id"]
        }

    def search_track(self, query):
        results = self._call_api("search", q=query, limit=5, type="track")
        if not results: return None
        
        tracks = results.get("tracks", {}).get("items", [])
        if not tracks: return None
        
        tracks.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        t = tracks[0]
        
        af = self.get_audio_features([t["id"]])[0]
        artist_data = self._call_api("artist", t["artists"][0]["id"])
        genre = artist_data["genres"][0] if artist_data and artist_data.get("genres") else "Unknown"

        return {
            "name": t["name"],
            "artist": t["artists"][0]["name"],
            "id": t["id"],
            "artist_id": t["artists"][0]["id"],
            "genre": genre,
            "preview_url": t.get("preview_url"),
            "target_features": af if af else None
        }

    def get_recommendations_from_spotify(self, seed_track_ids, limit=10):
        seeds = [str(tid) for tid in seed_track_ids if tid and str(tid) != "0"][:5]
        if not seeds: return []
        
        results = self._call_api("recommendations", seed_tracks=seeds, limit=limit)
        if not results: return []
        
        return [{
            "track_name": t["name"],
            "artist": t["artists"][0]["name"],
            "album": t["album"]["name"],
            "thumbnail": t["album"]["images"][0]["url"] if t["album"].get("images") else None,
            "duration_ms": t.get("duration_ms", 0),
            "popularity": t.get("popularity", 0),
            "spotify_id": t["id"]
        } for t in results["tracks"]]

    def repair_library_metadata(self):
        """Autonomously find and fix missing popularity, genres, and durations."""
        from .data_service import DataService
        from .audio_analysis_service import AudioAnalysisService
        import pandas as pd # Added import for pd.isna
        df = DataService.load_library()
        if df.empty: return False
        
        # 1. Selection: Find tracks with missing data (including thumbnails)
        mask = (df["popularity"] == 0) | (df["genre"] == "Unknown") | (df["thumbnail"].isna()) | (df["thumbnail"] == "")
        needs_repair = df[mask].copy()
        if needs_repair.empty: return True
        
        Logger.info("SPOTIFY", f"Starting library metadata repair for {len(needs_repair)} tracks...")
        
        # BATCHED FETCH: Spotify only allows batches of 50 for /tracks and /artists
        all_ids = needs_repair["spotify_id"].tolist()
        updated_rows = 0
        
        for i in range(0, len(all_ids), 50):
            batch_df = needs_repair.iloc[i:i+50]
            batch_ids = batch_df["spotify_id"].tolist()
            
            # ATTEMPT SPOTIFY FIRST
            sp_tracks = self.get_tracks(batch_ids)
            track_lookup = {t["id"]: t for t in sp_tracks if t}
            
            # Fetch Artists (for genres)
            artist_ids = list(set([t["artists"][0]["id"] for t in sp_tracks if t and t.get("artists")]))
            sp_artists = self.get_artists(artist_ids)
            artist_lookup = {a["id"]: a["genres"][0] if a.get("genres") else "Unknown" for a in sp_artists if a}
            
            # Update the library dataframe
            for idx, row in batch_df.iterrows():
                sid = row["spotify_id"]
                track = track_lookup.get(sid)
                
                # REPAIR WITH SPOTIFY DATA IF AVAILABLE
                if track:
                    mask = df["spotify_id"] == sid
                    if track.get("popularity", 0) > 0:
                        df.loc[mask, "popularity"] = track["popularity"]
                    if track.get("duration_ms", 0) > 0:
                        df.loc[mask, "duration_ms"] = track["duration_ms"]
                    if track.get("album") and track["album"].get("images"):
                        df.loc[mask, "thumbnail"] = track["album"]["images"][0]["url"]
                    if track.get("artists") and track["artists"][0]["id"] in artist_lookup:
                        df.loc[mask, "genre"] = artist_lookup[track["artists"][0]["id"]]
                
                # AUTONOMOUS iTunes FALLBACK (If still missing or Spotify failed)
                mask = df["spotify_id"] == sid
                lib_row = df.loc[mask].iloc[0]
                if (lib_row.get("popularity", 0) == 0) or (lib_row.get("genre") == "Unknown") or (not lib_row.get("thumbnail") or pd.isna(lib_row.get("thumbnail"))):
                    itunes = AudioAnalysisService.get_itunes_metadata(row["track_name"], row["artist"])
                    if itunes:
                        if lib_row.get("popularity", 0) == 0:
                            df.loc[mask, "popularity"] = itunes["popularity"]
                        if lib_row.get("genre") == "Unknown":
                            df.loc[mask, "genre"] = itunes["genre"]
                        if not lib_row.get("thumbnail") or pd.isna(lib_row.get("thumbnail")):
                            df.loc[mask, "thumbnail"] = itunes.get("thumbnail")
                        updated_rows += 1
                
                # Small sleep to be polite to iTunes
                time.sleep(0.1)
            
        if updated_rows > 0:
            DataService.save_library(df)
            Logger.info("SPOTIFY", f"Library repair completed. {updated_rows} tracks updated.")
            return True
        return False
