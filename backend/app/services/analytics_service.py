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
        # 1. Basic Counts
        total_plays = len(nebula_history)
        unique_tracks = len(set(t.spotify_id for t in nebula_history))
        
        # 2. Genre Distribution (from Artists)
        genres = []
        for artist in spotify_top_artists:
            genres.extend(artist.get("genres", []))
        genre_counts = Counter(genres).most_common(10)
        
        # 3. Audio DNA (from Features)
        # We filter out None values from Spotify API
        valid_features = [f for f in audio_features if f]
        dna = {
            "energy": mean([f["energy"] for f in valid_features]) if valid_features else 0,
            "danceability": mean([f["danceability"] for f in valid_features]) if valid_features else 0,
            "valence": mean([f["valence"] for f in valid_features]) if valid_features else 0,
            "tempo": mean([f["tempo"] for f in valid_features]) if valid_features else 0,
            "acousticness": mean([f["acousticness"] for f in valid_features]) if valid_features else 0,
        }

        # 4. Temporal Heatmap (Nebula Internal Data)
        # Activity by hour of the day
        hour_counts = Counter([t.played_at.hour for t in nebula_history if hasattr(t, 'played_at')])
        heatmap = [hour_counts.get(h, 0) for h in range(24)]

        # 5. Top Highlights
        top_nebula_tracks = Counter([t.spotify_id for t in nebula_history]).most_common(10)
        
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
            "activity": heatmap,
            "diversity_score": min(100, int((unique_tracks / (total_plays or 1)) * 100))
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

        return {
            "title": "Tu Odisea Musical",
            "identity": identity,
            "story_blocks": [
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
                    "highlight": f"{energy}% de Energía Musical",
                    "type": "radar"
                },
                {
                    "id": "insights",
                    "title": "Curiosidades sobre ti",
                    "text": insights[0] if insights else "Tu viaje musical es único.",
                    "type": "text"
                }
            ]
        }
