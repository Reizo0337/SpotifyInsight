import time
import requests
from ..core.spotify_auth import get_spotify_client
from ..core.logging import Logger

class SpotifyService:
    _forbidden_endpoints = set()
    
    def __init__(self):
        self.sp = get_spotify_client()
        if self.sp:
            try:
                user = self.sp.current_user()
                self.user_name = user["display_name"]
                self.user_id = user["id"]
                Logger.info("SPOTIFY", f"Connected as {self.user_name}")
            except Exception:
                self.sp = None # Disable if auth fails
                self.user_name = "Unknown"
                self.user_id = "Unknown"
        else:
            self.user_name = "Unknown"
            self.user_id = "Unknown"

    def is_connected(self):
        return self.sp is not None

    def _call_api(self, method_name, *args, **kwargs):
        """Wrapper for API calls with circuit breaker."""
        if not self.sp or method_name in self._forbidden_endpoints:
            return None
            
        try:
            func = getattr(self.sp, method_name)
            return func(*args, **kwargs)
        except Exception as e:
            msg = str(e)
            if "403" in msg or "Forbidden" in msg:
                Logger.error("SPOTIFY", f"Forbidden on {method_name}. Disabling for this session.")
                self._forbidden_endpoints.add(method_name)
            elif "429" in msg or "Rate limit" in msg:
                Logger.warning("SPOTIFY", f"Rate Limit (429) hit on {method_name}. Disabling all Spotify calls for now.")
                # Disable all major calls to avoid further blocking
                self._forbidden_endpoints.add("audio_features")
                self._forbidden_endpoints.add("current_user_top_tracks")
                self._forbidden_endpoints.add("current_user_recently_played")
                self._forbidden_endpoints.add("recommendations")
            else:
                Logger.error("SPOTIFY", f"API Error on {method_name}: {e}")
            return None

    def get_audio_features(self, track_ids):
        res = self._call_api("audio_features", track_ids)
        return res if res else [None] * len(track_ids)

    def get_artists(self, artist_ids):
        all_artists = []
        for i in range(0, len(artist_ids), 50):
            batch = artist_ids[i:i+50]
            res = self._call_api("artists", batch)
            if res and "artists" in res:
                all_artists.extend(res["artists"])
        return all_artists

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
        return {
            "track_name": track.get("name", "Unknown"),
            "artist": main_artist.get("name", "Unknown"),
            "artist_id": main_artist.get("id"),
            "album": track.get("album", {}).get("name", "Unknown"),
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
            "popularity": t.get("popularity", 0),
            "spotify_id": t["id"]
        } for t in results["tracks"]]
