import pandas as pd

class AnalysisService:
    @staticmethod
    def get_summary_stats(df):
        if df.empty:
            return {}
            
        # Ensure numeric columns are cleaned for JSON compliance
        cols = ["popularity", "danceability", "energy", "tempo", "valence"]
        temp_df = df.copy()
        for col in cols:
            if col in temp_df.columns:
                temp_df[col] = pd.to_numeric(temp_df[col], errors='coerce').fillna(0)

        stats = {
            "total_tracks": len(df),
            "avg_popularity": float(temp_df["popularity"].mean()) if "popularity" in temp_df.columns else 0.0,
            "avg_danceability": float(temp_df["danceability"].mean()) if "danceability" in temp_df.columns else 0.0,
            "avg_energy": float(temp_df["energy"].mean()) if "energy" in temp_df.columns else 0.0,
            "top_artists": df["artist"].value_counts().head(5).to_dict(),
            "top_genres": df[(df["genre"] != "Unknown") & (df["genre"].notna())]["genre"].value_counts().head(5).to_dict() if "genre" in df.columns else {},
            "avg_tempo": float(temp_df["tempo"].mean()) if "tempo" in temp_df.columns else 0.0,
            "avg_valence": float(temp_df["valence"].mean()) if "valence" in temp_df.columns else 0.0
        }
        return stats

    @staticmethod
    def get_genre_distribution(df):
        # Note: genre is not in our current track schema from spotify_service but we could add it
        # For now, let's use what we have or placeholder
        if "genre" in df.columns:
            return df["genre"].value_counts().to_dict()
        return {}
