import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

class SpotifyService:
    _forbidden_endpoints = set() # To skip 403-ing endpoints (Spotify API restrictions)
    def __init__(self):
        try:
            self.sp = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                    redirect_uri="http://127.0.0.1:8080/callback",
                    scope="user-top-read user-library-read user-read-recently-played playlist-read-private playlist-read-collaborative user-follow-read user-read-playback-state user-read-currently-playing user-modify-playback-state"
                    )
                )
            user = self.sp.current_user()
            self.user_name = user["display_name"] if user else "Unknown"
            self.user_id = user["id"] if user else "Unknown"
            print(f"[SPOTIFY] Connected as {self.user_name} ({self.user_id})")
        except Exception as e:
            print(f"[SPOTIFY] Auth Error: {e}")
            self.sp = None
            self.user_name = "Unknown"
            self.user_id = "Unknown"

    def is_connected(self):
        return self.sp is not None

    def get_audio_features(self, track_ids):
        """Fetch audio features with circuit breaker protection."""
        if not self.sp or "audio_features" in SpotifyService._forbidden_endpoints:
            return [None] * len(track_ids)
        
        try:
            return self.sp.audio_features(track_ids)
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                print(f"[SPOTIFY] !!! 403 FORBIDDEN DETECTED on audio_features !!! Skipping for this session.")
                SpotifyService._forbidden_endpoints.add("audio_features")
            return [None] * len(track_ids)

    def get_artists(self, artist_ids):
        """Fetch artists data with circuit breaker protection."""
        if not self.sp or "artists" in SpotifyService._forbidden_endpoints:
            return []
            
        try:
            # Spotify allows 50 artists per request
            all_artists = []
            for i in range(0, len(artist_ids), 50):
                batch = artist_ids[i:i+50]
                results = self.sp.artists(batch)
                if results and "artists" in results:
                    all_artists.extend(results["artists"])
            return all_artists
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                print(f"[SPOTIFY] !!! 403 FORBIDDEN DETECTED on artists !!! Skipping for this session.")
                SpotifyService._forbidden_endpoints.add("artists")
            return []

    def get_top_tracks_with_features(self, limit=50):
        import time
        t_start = time.time()
        if not self.sp: return []
        
        results = self.sp.current_user_top_tracks(time_range="medium_term", limit=limit)
        tracks = results["items"]
        if not tracks: return []
            
        track_ids = [t["id"] for t in tracks]
        
        # Optimization: Use global cached index
        from .data_service import DataService
        DataService.load_library() # Ensures cache is populated
        
        lib_lookup = DataService._library_indexed_cache
        
        final_features = {}
        missing_ids = []
        
        for tid in track_ids:
            if lib_lookup is not None and tid in lib_lookup.index:
                final_features[tid] = lib_lookup.loc[tid].to_dict()
            else:
                missing_ids.append(tid)
        
        if missing_ids:
            t_af = time.time()
            af_list = self.get_audio_features(missing_ids)
            for idx, af in enumerate(af_list):
                if af:
                    final_features[missing_ids[idx]] = af
            print(f"[SPOTIFY] audio_features processed in {time.time()-t_af:.3f}s")

        # Artist genres
        t_genre = time.time()
        artist_ids = list(set([t["artists"][0]["id"] for t in tracks if t.get("artists")]))
        artist_genres = {}
        
        artists_data = self.get_artists(artist_ids)
        for artist in artists_data:
            if artist and artist.get("genres"):
                artist_genres[artist["id"]] = artist["genres"][0]
        
        print(f"[SPOTIFY] Genre fetching processed in {time.time()-t_genre:.3f}s")
        
        data = []
        for track in tracks:
            tid = track["id"]
            feat = final_features.get(tid, {})
            main_artist = track["artists"][0] if track.get("artists") else {}
            data.append({
                "track_name": track.get("name", "Unknown"),
                "artist": main_artist.get("name", "Unknown"),
                "artist_id": main_artist.get("id"),
                "album": track.get("album", {}).get("name", "Unknown"),
                "popularity": track.get("popularity", 0),
                "genre": artist_genres.get(main_artist.get("id"), "Unknown"),
                "danceability": feat.get("danceability", 0),
                "energy": feat.get("energy", 0),
                "tempo": feat.get("tempo", 0),
                "valence": feat.get("valence", 0),
                "acousticness": feat.get("acousticness", 0),
                "instrumentalness": feat.get("instrumentalness", 0),
                "speechiness": feat.get("speechiness", 0),
                "loudness": feat.get("loudness", 0),
                "key": feat.get("key", 0),
                "mode": feat.get("mode", 0),
                "spotify_id": tid
            })
        print(f"[SPOTIFY] get_top_tracks processed in {time.time()-t_start:.3f}s")
        return data

    def get_recently_played_with_features(self, limit=50):
        import time
        t_start = time.time()
        if not self.sp: return []
        results = self.sp.current_user_recently_played(limit=limit)
        tracks = [item["track"] for item in results["items"] if item.get("track")]
        if not tracks: return []
            
        track_ids = [t["id"] for t in tracks if t.get("id")]
        
        # Optimization: Use global cached index
        from .data_service import DataService
        DataService.load_library()
        
        lib_lookup = DataService._library_indexed_cache
        
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
                if af:
                    final_features[missing_ids[idx]] = af
            
        # Fetch artist genres
        artist_genres = {}
        artist_ids = list(set([t["artists"][0]["id"] for t in tracks if t.get("artists")]))
        artists_data = self.get_artists(artist_ids)
        for artist in artists_data:
            if artist and artist.get("genres"):
                artist_genres[artist["id"]] = artist["genres"][0]

        data = []
        for i, track in enumerate(tracks):
            tid = track["id"]
            feat = final_features.get(tid, {})
            main_artist = track["artists"][0] if track.get("artists") else {}
            data.append({
                "track_name": track.get("name", "Unknown"),
                "artist": main_artist.get("name", "Unknown"),
                "artist_id": main_artist.get("id"),
                "album": track.get("album", {}).get("name", "Unknown"),
                "popularity": track.get("popularity", 0),
                "genre": artist_genres.get(main_artist.get("id"), "Unknown"),
                "danceability": feat.get("danceability", 0),
                "energy": feat.get("energy", 0),
                "tempo": feat.get("tempo", 0),
                "valence": feat.get("valence", 0),
                "acousticness": feat.get("acousticness", 0),
                "instrumentalness": feat.get("instrumentalness", 0),
                "speechiness": feat.get("speechiness", 0),
                "loudness": feat.get("loudness", 0),
                "key": feat.get("key", 0),
                "mode": feat.get("mode", 0),
                "spotify_id": tid
            })
        print(f"[SPOTIFY] get_recently_played processed in {time.time()-t_start:.3f}s")
        return data

    def search_track(self, query):
        # Buscamos los 5 temas más relevantes para el query
        results = self.sp.search(q=query, limit=5, type="track")
        tracks = results.get("tracks", {}).get("items", [])
        if tracks:
            # Ordenamos por popularidad para evitar "versiones" o temas irrelevantes
            tracks.sort(key=lambda x: x.get("popularity", 0), reverse=True)
            t = tracks[0]
            
            # Fetch audio features AND genre for the winner
            features = {}
            genre = "Unknown"
            try:
                # Get features
                af = self.sp.audio_features([t["id"]])
                if af and af[0]:
                    features = af[0]
                
                # Get genre from artist metadata
                artist_data = self.sp.artist(t["artists"][0]["id"])
                if artist_data.get("genres"):
                    genre = artist_data["genres"][0]
            except Exception:
                pass

            return {
                "name": t["name"],
                "artist": t["artists"][0]["name"],
                "id": t["id"],
                "artist_id": t["artists"][0]["id"],
                "genre": genre,
                "preview_url": t.get("preview_url"),
                "target_features": {
                    "danceability": features.get("danceability", 0),
                    "energy": features.get("energy", 0),
                    "tempo": features.get("tempo", 0),
                    "valence": features.get("valence", 0),
                    "acousticness": features.get("acousticness", 0),
                    "instrumentalness": features.get("instrumentalness", 0),
                    "speechiness": features.get("speechiness", 0),
                    "loudness": features.get("loudness", 0),
                    "key": features.get("key", 0),
                    "mode": features.get("mode", 0)
                } if features else None
            }
        return None

    def get_recommendations_weighted(self, target_track, user_taste_ids, limit=10):
        if not self.sp: return []
        
        seed_song_id = target_track["id"]
        seed_artist_id = target_track.get("artist_id")
        
        # Obtener historial para filtrar (no recomendar lo que ya conoce)
        past_ids = set()
        try:
            import pandas as pd
            LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed", "saved_tracks.csv")
            if os.path.exists(LIBRARY_PATH):
                df_lib = pd.read_csv(LIBRARY_PATH)
                past_ids = set(df_lib["spotify_id"].dropna().unique())
        except Exception:
            pass

        # Ajuste de Pesos: 80% Canción / 20% Gustos
        # Para 5 semillas: 4 semillas de la búsqueda (80%) + 1 de gustos (20%)
        seeds = [seed_song_id]
        if seed_artist_id:
            seeds.append(seed_artist_id) # Usar el artista ayuda a fijar el género al 80%
            seeds.append(seed_song_id)   # Repetir para reforzar peso (según comportamiento observado en API)
            seeds.append(seed_artist_id)
        else:
            seeds.extend([seed_song_id] * 3)

        # Limpiar y SHUFFLE de los gustos del usuario
        import random
        clean_user_seeds = [str(tid) for tid in user_taste_ids if tid and str(tid) != "0"]
        random.shuffle(clean_user_seeds)

        seeds.append(clean_user_seeds[0] if clean_user_seeds else seed_song_id) # 20% Gustos
        
        # Eliminar posibles duplicados manteniendo el orden
        final_seeds = list(dict.fromkeys(seeds))[:5]
        
        attempts = []
        
        # Filtramos seeds para que no haya Nones en las peticiones
        tracks_only = [s for s in final_seeds if s != seed_artist_id]
        artists_only = [seed_artist_id] if seed_artist_id and seed_artist_id in final_seeds else []
        
        if tracks_only or artists_only:
            attempts.append({"seed_tracks": tracks_only if tracks_only else None, 
                             "seed_artists": artists_only if artists_only else None})
        
        attempts.append({"seed_tracks": [seed_song_id]})
        
        # New attempt with audio feature targets if provided
        if "target_features" in target_track:
            tf = target_track["target_features"]
            attempts.append({
                "seed_tracks": [seed_song_id],
                "target_danceability": tf.get("danceability"),
                "target_energy": tf.get("energy"),
                "target_valence": tf.get("valence")
            })
        
        if seed_artist_id:
            attempts.append({"seed_artists": [seed_artist_id]})

        for attempt in attempts:
            if not attempt: continue
            try:
                # Intentamos obtener más (limit * 2) para poder filtrar los ya escuchados
                results = self._fetch_recs(limit=limit*3, **attempt)
                # Filtrar duplicados del historial
                filtered = [r for r in results if r["spotify_id"] not in past_ids and r["spotify_id"] != seed_song_id]
                if filtered:
                    return filtered[:limit]
            except Exception:
                continue
        
        # FALLBACK 1: Top Tracks (Filtrados)
        try:
            if seed_artist_id:
                results = self.sp.artist_top_tracks(seed_artist_id)["tracks"]
                filtered = [t for t in results if t["id"] not in past_ids]
                if filtered:
                    return [{
                        "track_name": t["name"],
                        "artist": t["artists"][0]["name"],
                        "album": t["album"]["name"],
                        "popularity": t.get("popularity", 0),
                        "spotify_id": t["id"]
                    } for t in filtered[:limit]]
        except Exception:
            pass

        # FALLBACK FINAL: Historial aleatorio (para que no sea siempre el mismo)
        try:
            import pandas as pd
            import numpy as np
            DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed", "user_tracks.csv")
            if os.path.exists(DATA_PATH):
                df = pd.read_csv(DATA_PATH)
                if not df.empty:
                    # Devolver una muestra aleatoria en lugar de los últimos 10 siempre
                    sample = df.sample(min(limit, len(df))).replace({np.nan: None})
                    return sample.to_dict(orient="records")
        except Exception:
            pass
            
        return []

    def _fetch_recs(self, limit, seed_tracks=None, seed_artists=None, market=None, **kwargs):
        if not self.sp: return []
        # Importante: spotipy usa 'country' para el market en recommendations
        results = self.sp.recommendations(seed_tracks=seed_tracks, seed_artists=seed_artists, limit=limit, country=market, **kwargs)
        return [{
            "track_name": t["name"],
            "artist": t["artists"][0]["name"],
            "album": t["album"]["name"],
            "popularity": t.get("popularity", 0),
            "spotify_id": t["id"]
        } for t in results["tracks"]]

    def get_recommendations_from_spotify(self, seed_track_ids, limit=10):
        if not seed_track_ids:
            return []
            
        # Ensure seed_track_ids are cleaned (no Nones, no empty strings)
        seeds = [str(tid) for tid in seed_track_ids if tid and str(tid) != "0"][:5]
        
        if not seeds:
            return []

        try:
            results = self.sp.recommendations(seed_tracks=seeds, limit=limit)
            recs = []
            for track in results["tracks"]:
                recs.append({
                    "track_name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                    "popularity": track.get("popularity", 0),
                    "spotify_id": track["id"]
                })
            return recs
        except Exception as e:
            print(f"Error fetching recommendations from Spotify (Fallback 1 failed): {e}")
            # Fallback 2: If everything fails, just return some random top tracks
            try:
                top = self.sp.current_user_top_tracks(limit=limit)["items"]
                return [{
                    "track_name": t["name"],
                    "artist": t["artists"][0]["name"],
                    "album": t["album"]["name"],
                    "popularity": t.get("popularity", 0),
                    "spotify_id": t["id"]
                } for t in top]
            except Exception:
                return []
