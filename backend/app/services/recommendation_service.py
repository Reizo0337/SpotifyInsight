from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np

class RecommendationService:
    @staticmethod
    def get_recommendations(df, user_profile_tracks=None, n_recommendations=10):
        if df.empty or len(df) < 2:
            return []
            
        features = ["danceability", "energy", "tempo", "valence", "popularity"]
        
        # Check if we have valid features (not all zeros)
        if (df[features] == 0).all().all():
            # If all features are zero, we can't use cosine similarity
            # Returning empty list to trigger fallback in the API layer
            return []

        # Ensure data is numeric
        data = df[features].fillna(0).values
        
        # If no profile provided, use the last 5 tracks as seed
        if user_profile_tracks is None:
            user_profile = data[-5:].mean(axis=0).reshape(1, -1)
        else:
            user_profile = user_profile_tracks[features].mean(axis=0).values.reshape(1, -1)
            
        similarities = cosine_similarity(user_profile, data)
        # Flatten similarities and get top indices
        sim_scores = similarities.flatten()
        
        # Sort indices by similarity
        recommended_indices = np.argsort(sim_scores)[::-1]
        
        # Filter out tracks already in "user profile" if needed, 
        # but for now just return top N unique tracks
        recommendations = df.iloc[recommended_indices].head(n_recommendations + 10)
        recommendations = recommendations.drop_duplicates(subset=["track_name", "artist"]).head(n_recommendations)
        
        # Clean data for JSON serialization (convert NaN to None and ensure Python types)
        clean_recs = recommendations.replace({np.nan: None}).to_dict(orient="records")
        return clean_recs
