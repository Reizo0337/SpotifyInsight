import time
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from ..core.logging import Logger

class RecommendationService:
    FEATURES = [
        "danceability", "energy", "tempo", "valence", 
        "acousticness", "instrumentalness", "speechiness", 
        "loudness", "key", "mode"
    ]

    @classmethod
    def get_recommendations(cls, df, user_profile_tracks=None, n_recommendations=10, spotify_candidates=None):
        """Generates hybrid recommendations with temporal weighting and Spotify candidate merging."""
        start_time = time.time()
        
        if df.empty or len(df) < 2:
            return spotify_candidates[:n_recommendations] if spotify_candidates else []
            
        # 1. Prepare candidates
        analyzed_df = df[df["energy"] != 0].copy()
        
        # 2. Add temporal weighting (favor more recent additions)
        if "played_at" in analyzed_df.columns:
            # Scale from 1.0 (newest) to 0.7 (oldest)
            max_t = analyzed_df["played_at"].max()
            min_t = analyzed_df["played_at"].min()
            if max_t > min_t:
                analyzed_df["temp_weight"] = 0.7 + 0.3 * (analyzed_df["played_at"] - min_t) / (max_t - min_t)
            else:
                analyzed_df["temp_weight"] = 1.0
        else:
            analyzed_df["temp_weight"] = 1.0

        # 3. Feature Matrix and User Profile
        X = cls._prepare_feature_matrix(analyzed_df)
        user_profile = cls._build_user_profile(X, user_profile_tracks)
        
        # 4. Similarity Computation
        similarities = cosine_similarity(user_profile, X).flatten()
        # Apply temporal weight
        similarities = similarities * analyzed_df["temp_weight"].values
        
        # 5. Ranking
        indices = np.argsort(similarities)[::-1]
        local_recs = analyzed_df.iloc[indices].head(n_recommendations * 2)
        
        # 6. Hybrid Merge
        if spotify_candidates:
            # Merge and de-duplicate
            combined = pd.concat([pd.DataFrame(spotify_candidates), local_recs]).drop_duplicates(subset=["spotify_id"])
            # Re-rank combined by similarity if possible, else just interleave
            final_recs = combined.head(n_recommendations)
        else:
            final_recs = local_recs.head(n_recommendations)
            
        result = final_recs.replace({np.nan: None}).to_dict(orient="records")
        Logger.time("REC", f"Hybrid recommendations generated ({'Spotify' if spotify_candidates else 'Local'} led)", start_time)
        return result

    @classmethod
    def _prepare_feature_matrix(cls, df):
        """Extracts and normalizes features for similarity computation."""
        X = df[cls.FEATURES].fillna(0).values.copy()
        
        # Individual scaling for non-0-1 features
        if "tempo" in cls.FEATURES:
            idx = cls.FEATURES.index("tempo")
            X[:, idx] /= 250.0 # Normalized BPM
            
        if "loudness" in cls.FEATURES:
            idx = cls.FEATURES.index("loudness")
            # Convert -60..0 to 0..1
            X[:, idx] = (X[:, idx] + 60) / 60.0
            
        return X

    @classmethod
    def _build_user_profile(cls, X, user_profile_tracks):
        """Creates a weighted vector representing user taste."""
        if user_profile_tracks is None or user_profile_tracks.empty:
            # Fallback: weight the most recent tracks more heavily
            sample_size = min(100, len(X))
            recent_X = X[-sample_size:]
            weights = np.linspace(0.1, 1.0, len(recent_X))
            return np.average(recent_X, axis=0, weights=weights).reshape(1, -1)
        
        # If we have explicit user history
        profile_x = cls._prepare_feature_matrix(user_profile_tracks)
        return np.mean(profile_x, axis=0).reshape(1, -1)
