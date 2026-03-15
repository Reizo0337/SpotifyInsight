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
    def get_recommendations(cls, df, user_profile_tracks=None, n_recommendations=10):
        """Generates hybrid recommendations based on user taste profile."""
        start_time = time.time()
        
        if df.empty or len(df) < 2:
            Logger.info("REC", f"Insufficient data: df empty={df.empty}, len={len(df)}")
            return []
            
        # 1. Filter for analyzed tracks
        analyzed_df = df[df["energy"] != 0].copy()
        if len(analyzed_df) < 5:
            Logger.info("REC", "Not enough analyzed tracks, using popularity fallback")
            recs = df.sort_values("popularity", ascending=False).head(n_recommendations)
            return recs.replace({np.nan: None}).to_dict(orient="records")

        # 2. Performance Sampling for massive libraries
        if len(analyzed_df) > 500000:
            analyzed_df = pd.concat([
                analyzed_df.tail(20000), 
                analyzed_df.head(len(analyzed_df)-20000).sample(n=480000)
            ])

        # 3. Feature Matrix Preparation
        X = cls._prepare_feature_matrix(analyzed_df)
        
        # 4. User Profile Building
        user_profile = cls._build_user_profile(X, user_profile_tracks)
        
        # 5. Similarity Computation
        t_sim = time.time()
        similarities = cosine_similarity(user_profile, X).flatten()
        
        # 6. Ranking and Cleanup
        indices = np.argsort(similarities)[::-1]
        recs = analyzed_df.iloc[indices].head(n_recommendations + 30)
        recs = recs.drop_duplicates(subset=["track_name", "artist"]).head(n_recommendations)
        
        result = recs.replace({np.nan: None}).to_dict(orient="records")
        Logger.time("REC", "Recommendations generated", start_time)
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
