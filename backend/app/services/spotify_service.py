import time
import requests
from ..core.spotify_auth import get_spotify_client
from ..core.logging import Logger

class SpotifyService:
    _forbidden_endpoints = set()
    _last_429_time = 0
    _429_COOLDOWN = 60 

    def __init__(self, token_info: dict = None):
        self.sp = None
        self.user_name = "Invitado"
        self.user_id = "local_nebula"
        
        if token_info:
            from ..core.spotify_auth import get_spotify_client_from_token
            try:
                self.sp, self.updated_token_info = get_spotify_client_from_token(token_info)
                # We no longer block the thread with a "me" call on init. 
                # Frequency calibration will happen on the first meaningful signal transmission.
            except:
                self.sp = None
                self.updated_token_info = None
        else:
            self.updated_token_info = None
            from ..core.spotify_auth import get_spotify_client
            try:
                self.sp = get_spotify_client()
            except: pass

    def is_connected(self):
        return self.sp is not None

    def get_user_profile(self):
        return {"user_name": self.user_name, "user_id": self.user_id}

    def _call_api(self, method_name, *args, **kwargs):
        """Wrapper for API calls with circuit breaker."""
        if not self.sp or "ALL" in self._forbidden_endpoints:
            return None
            
        try:
            func = getattr(self.sp, method_name)
            return func(*args, **kwargs)
        except Exception as e:
            msg = str(e).lower()
            if "403" in msg or "forbidden" in msg:
                Logger.warning("SPOTIFY", f"Access forbidden on {method_name} - potentially restricted by Spotify.")
            elif "429" in msg or "rate limit" in msg:
                Logger.warning("SPOTIFY", f"Rate Limit (429)")
                self._forbidden_endpoints.add("ALL")
                self._last_429_time = time.time()
            return None

    def get_audio_features(self, track_ids):
        """Fetch technical audio features with 403 safety."""
        if not track_ids: return []
        res = self._call_api("audio_features", track_ids)
        if not res: return [None] * len(track_ids)
        return res

    def get_tracks(self, track_ids):
        if not track_ids: return []
        all_tracks = []
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i+50]
            res = self._call_api("tracks", batch)
            if res and "tracks" in res:
                all_tracks.extend(res["tracks"])
        return all_tracks

    def sync_user_library(self):
        """Fetches Liked Songs."""
        if not self.sp: return []
        
        all_tracks = []
        try:
            results = self._call_api("current_user_saved_tracks", limit=20)
            while results:
                for item in results.get('items', []):
                    t = item.get('track')
                    if t:
                        all_tracks.append({
                            "id": t["id"],
                            "name": t["name"],
                            "artists": t.get("artists", []),
                            "album": t.get("album", {})
                        })
                
                if len(all_tracks) >= 100: break # Hard limit for now to keep it fast
                if results.get('next'):
                    results = self._call_api("next", results)
                else:
                    results = None
        except: pass
        return all_tracks

    def search_tracks(self, query, limit=10):
        results = self._call_api("search", q=query, limit=limit, type="track")
        if not results: return []
        return results.get("tracks", {}).get("items", [])

    def get_recommendations_from_spotify(self, seed_tracks, limit=10):
        seeds = [str(tid) for tid in seed_tracks if tid and len(str(tid)) > 10][:5]
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

    def get_user_playlists(self, limit=50):
        if not self.sp: 
            Logger.error("SPOTIFY", "Cannot fetch playlists: Client not initialized.")
            return []
        try:
            results = self._call_api("current_user_playlists", limit=limit)
            if not results:
                # Fallback: maybe we need the explicit user_id
                user = self._call_api("me")
                if user:
                    results = self._call_api("user_playlists", user=user['id'], limit=limit)
            
            playlists = []
            for it in results.get("items", []):
                if not it: continue
                
                # Robust track count detection (Spotify deprecated 'tracks' for 'items' recently)
                t_obj = it.get("items") or it.get("tracks") or {}
                t_count = 0
                if isinstance(t_obj, dict):
                    t_count = t_obj.get("total", 0)
                elif isinstance(t_obj, int):
                    t_count = t_obj
                
                playlists.append({
                    "id": it["id"],
                    "name": it["name"],
                    "thumbnail": it["images"][0]["url"] if it.get("images") and len(it["images"]) > 0 else None,
                    "track_count": t_count,
                    "owner": it.get("owner", {}).get("display_name", "Desconocido") if isinstance(it.get("owner"), dict) else "Desconocido",
                    "is_public": it.get("public", True)
                })
            return playlists
        except Exception as e:
            Logger.error("SPOTIFY", f"Failed to fetch playlists: {str(e)}")
            return []

    def get_playlist_tracks(self, playlist_id, limit=100, offset=0):
        """Fetches tracks from a playlist using the official API (No 100-track embed limit)."""
        if not self.sp: return []
        results = self._call_api("playlist_items", playlist_id, limit=limit, offset=offset)
        if not results: return []
        
        tracks = []
        for item in results.get("items", []):
            if not item.get("track"): continue
            t = item["track"]
            tracks.append({
                "track_name": t["name"],
                "artist": t["artists"][0]["name"] if t.get("artists") else "Unknown Artist",
                "album": t["album"]["name"] if t.get("album") else "Unknown Album",
                "thumbnail": t["album"]["images"][0]["url"] if t.get("album") and t["album"].get("images") else None,
                "spotify_id": t["id"],
                "duration_ms": t.get("duration_ms", 0),
                "popularity": t.get("popularity", 0)
            })
        return tracks

    def get_playlist_metadata(self, playlist_id):
        """Fetches basic playlist info (name, thumbnail, total count)."""
        if not self.sp: return None
        res = self._call_api("playlist", playlist_id)
        if not res: return None
        
        images = res.get("images", [])
        tracks_obj = res.get("tracks", {})
        count = 0
        if isinstance(tracks_obj, dict):
            count = tracks_obj.get("total", 0)
        elif isinstance(tracks_obj, int):
            count = tracks_obj
            
        return {
            "id": res.get("id", playlist_id),
            "name": res.get("name", "Unknown Playlist"),
            "thumbnail": images[0]["url"] if images else None,
            "track_count": count,
            "owner": res.get("owner", {}).get("display_name", "Autor de Spotify"),
            "is_public": res.get("public", True)
        }

    def get_user_top_artists(self, limit=20, time_range="medium_term"):
        """Resolves user's top signal emitters directly from Spotify core."""
        res = self._call_api("current_user_top_artists", limit=limit, time_range=time_range)
        if not res: return []
        return [{
            "id": a["id"],
            "name": a["name"],
            "genres": a.get("genres", []),
            "thumbnail": a["images"][0]["url"] if a.get("images") else None,
            "popularity": a.get("popularity", 0)
        } for a in res.get("items", [])]

    def get_user_top_tracks(self, limit=20, time_range="medium_term"):
        """Identifies elite tracks using Spotify's internal algorithm."""
        res = self._call_api("current_user_top_tracks", limit=limit, time_range=time_range)
        if not res: return []
        return [{
            "track_name": t["name"],
            "artist": t["artists"][0]["name"],
            "album": t["album"]["name"],
            "thumbnail": t["album"]["images"][0]["url"] if t["album"].get("images") else None,
            "spotify_id": t["id"],
            "duration_ms": t.get("duration_ms", 0),
            "popularity": t.get("popularity", 0)
        } for t in res.get("items", [])]

    def get_recently_played(self, limit=20):
        res = self._call_api("current_user_recently_played", limit=limit)
        if not res: return []
        return [{
            "track_name": it["track"]["name"],
            "artist": it["track"]["artists"][0]["name"],
            "spotify_id": it["track"]["id"],
            "duration_ms": it["track"].get("duration_ms", 0)
        } for it in res.get("items", [])]
