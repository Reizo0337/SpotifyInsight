import math
from collections import Counter
from datetime import datetime
from statistics import mean

class AnalyticsService:
    @staticmethod
    def calculate_stats(nebula_history, spotify_top_tracks, spotify_top_artists, audio_features):
        """
        Processes multi-source musical signals into advanced KPIs and visualization datasets.
        """
        def safe_mean(data, ignore_zeros=False):
            if not data: return 0
            nums = [float(x) for x in data if x is not None]
            if ignore_zeros:
                nums = [n for n in nums if n > 0]
            if not nums: return 0
            
            if ignore_zeros: # Tempo normalization
                adjusted = []
                for n in nums:
                    if n < 90: adjusted.append(n * 2) 
                    else: adjusted.append(n)
                nums = adjusted
            return mean(nums) if nums else 0

        def infer_genre(f):
            e, t, v, d = f.get('energy', 0), f.get('tempo', 0), f.get('valence', 0), f.get('danceability', 0)
            if e > 0.7 and t > 130: return "Techno / Hard Dance"
            if v > 0.6 and d > 0.6: return "Pop / Vibrant"
            if e < 0.4 and t < 100: return "Chill / Ambient"
            if d > 0.8: return "Dance/Club"
            return "Indie/Alternative"

        # 1. Aggregated Intelligence
        local_ids = [t.spotify_id for t in nebula_history]
        spotify_ids = [t.get("spotify_id") or t.get("id") for t in spotify_top_tracks]
        all_unique_ids = set(local_ids + spotify_ids)
        total_plays = len(nebula_history) + len(spotify_top_tracks)
        unique_tracks = len(all_unique_ids)

        # 2. Advanced Genre Extraction
        genres = []
        for artist in spotify_top_artists:
            if artist:
                genres.extend(artist.get("genres", []))
        
        for h in nebula_history:
            if hasattr(h, 'genres') and h.genres:
                genres.extend(h.genres)
            elif hasattr(h, 'energy') and h.energy > 0:
                inferred = infer_genre({
                    "energy": h.energy,
                    "tempo": getattr(h, 'tempo', 0),
                    "valence": getattr(h, 'valence', 0),
                    "danceability": getattr(h, 'danceability', 0)
                })
                genres.append(inferred)

        genre_counts = Counter(genres).most_common(10)
        
        # 3. Audio DNA (Combined Signals)
        # Extract features from Spotify Top Tracks
        all_signals = [f for f in audio_features if f]
        
        # ALSO extract features from Nebula History
        for h in nebula_history:
            if hasattr(h, 'energy') and h.energy is not None and h.energy > 0:
                all_signals.append({
                    "energy": h.energy,
                    "danceability": getattr(h, 'danceability', 0),
                    "valence": getattr(h, 'valence', 0),
                    "tempo": getattr(h, 'tempo', 0)
                })

        dna = {
            "energy": safe_mean([f.get("energy") for f in all_signals]),
            "danceability": safe_mean([f.get("danceability") for f in all_signals]),
            "valence": safe_mean([f.get("valence") for f in all_signals]),
            "tempo": safe_mean([f.get("tempo") for f in all_signals], ignore_zeros=True),
        }

        # 4. Temporal Heatmap (Nebula Internal Data)
        heatmap = [0] * 24
        for t in nebula_history:
            if hasattr(t, 'played_at') and t.played_at:
                heatmap[t.played_at.hour] += 1

        # 5. Top Highlights (Combined)
        all_artists = [getattr(t, 'artist', 'Unknown') for t in (nebula_history)]
        for track in spotify_top_tracks:
             artists = track.get("artists", [])
             if artists: all_artists.append(artists[0].get("name", "Unknown"))
             else: all_artists.append(track.get("artist", "Unknown"))
        
        artist_counts = Counter([a for a in all_artists if a != "Unknown"]).most_common(10)
        
        # Top Tracks from Nebula History
        # We need more than just ID, we need name/artist for display
        track_map = {}
        for h in nebula_history:
            sid = h.spotify_id
            if sid not in track_map:
                # Assuming nebula_history objects have track metadata attached if possible
                # In music.py we passed nebula_data which are History objects
                # But in loop we enriched them with some features.
                # Actually, in calculate_stats nebula_history is just a list of objects.
                pass
        
        # Top Tracks from Nebula History
        # Count sessions by ID and then map back to metadata
        track_plays = Counter([h.spotify_id for h in nebula_history]).most_common(12)
        top_tracks = []
        
        # Create a lookup for data
        meta_lookup = {h.spotify_id: h for h in nebula_history if hasattr(h, 'track_name')}
        
        for sid, count in track_plays:
            meta = meta_lookup.get(sid)
            if meta:
                top_tracks.append({
                    "spotify_id": sid,
                    "name": getattr(meta, 'track_name', 'Unknown'),
                    "artist": getattr(meta, 'artist', 'Unknown'),
                    "thumbnail": getattr(meta, 'thumbnail', ''),
                    "count": count
                })

        return {
            "kpis": {
                "total_plays": total_plays,
                "unique_tracks": unique_tracks,
                "loyalty_ratio": round(total_plays / unique_tracks, 2) if unique_tracks > 0 else 0,
                "musical_energy": round(dna["energy"] * 100, 1),
                "rhythm_stability": round(dna["tempo"], 1),
                "emotional_valence": round(dna["valence"] * 100, 1)
            },
            "dna": dna,
            "genres": [{"name": g[0], "value": g[1]} for g in genre_counts],
            "top_artists": [{"name": a[0], "count": a[1]} for a in artist_counts],
            "top_tracks": top_tracks,
            "activity": heatmap,
            "diversity_score": min(100, int((unique_tracks / (total_plays or 1)) * 100)),
            "chronology": [
                {
                    "year": int(t.release_date[:4]) if (hasattr(t, 'release_date') and t.release_date and len(t.release_date) >= 4) else 2024,
                    "val": getattr(t, 'energy', 0.5) * 100, # Y-axis can be energy for "vibe over time"
                    "name": getattr(t, 'track_name', 'Unknown'),
                    "artist": getattr(t, 'artist', 'Unknown'),
                    "thumb": getattr(t, 'thumbnail', '')
                }
                for t in nebula_history if hasattr(t, 'release_date') and t.release_date
            ]
        }

    @staticmethod
    def generate_wrapped_story(stats):
        """
        Generates a narrative storytelling structure for the 'Wrapped' mode.
        """
        energy = stats["kpis"]["musical_energy"]
        valence = stats["kpis"]["emotional_valence"]
        
        # 1. Identity Tag
        identity = "Explorador de Sonidos"
        if energy > 70 and valence > 60: identity = "Vibración Pura"
        elif energy > 70: identity = "Dinamismo Eléctrico"
        elif energy < 40 and valence < 40: identity = "Profundidad Nocturna"
        elif valence > 75: identity = "Luz Radiante"
        
        # 2. Insights
        insights = []
        if stats["activity"][22] > 0 or stats["activity"][23] > 0 or stats["activity"][0] > 0:
            insights.append("Eres una criatura nocturna. Tu música alcanza el clímax mientras el mundo duerme.")
        
        if stats["diversity_score"] > 80:
            insights.append("Tu curiosidad no tiene fronteras. Pocas canciones se repiten en tu radar.")
        elif stats["diversity_score"] < 30:
            insights.append("Cuando amas una canción, la exprimes hasta el final. Lealtad sonora absoluta.")

        # 3. Top Highlights
        top_artist = stats["top_artists"][0]["name"] if stats.get("top_artists") else "Nebula Explorer"
        top_track = stats["top_tracks"][0] if stats.get("top_tracks") else None
        
        story = [
                {
                    "id": "intro",
                    "title": "Bienvenido a tu Universo",
                    "text": f"Has procesado {stats['kpis']['total_plays']} pulsaciones musicales en Nebula.",
                    "type": "cover"
                },
                {
                    "id": "vibe",
                    "title": "Tu ADN Sonoro",
                    "text": f"Tu vibración dominante es {identity}.",
                    "highlight": f"{energy}% de Energía",
                    "type": "radar"
                },
                {
                    "id": "artist",
                    "title": "Tu Órbita Principal",
                    "text": f"Tu gravedad ha sido dominada por un solo nombre.",
                    "highlight": top_artist,
                    "type": "text"
                }
        ]

        if top_track:
            story.append({
                "id": "track",
                "title": "Tu Himno Estelar",
                "text": f"Esta canción ha resonado en tus sistemas {top_track['count']} veces.",
                "highlight": top_track["name"],
                "type": "text"
            })

        if insights:
            story.append({
                "id": "insights",
                "title": "Curiosidades sobre ti",
                "text": insights[0],
                "type": "text"
            })
            
        story.append({
            "id": "outro",
            "title": "Fin del Viaje Temporal",
            "text": "Tu historia sigue escribiéndose en las estrellas.",
            "highlight": "NEBULA 2026",
            "type": "cover"
        })

        return {
            "title": "Tu Odisea Musical",
            "identity": identity,
            "story_blocks": story
        }
