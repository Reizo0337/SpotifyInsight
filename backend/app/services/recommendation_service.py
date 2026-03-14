from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

class RecommendationService:
    @staticmethod
    def get_recommendations(df, user_profile_tracks=None, n_recommendations=10):
        if df.empty or len(df) < 2:
            return []
            
        # 1. Define Features
        features = [
            "danceability", "energy", "tempo", "valence", 
            "acousticness", "instrumentalness", "speechiness", 
            "loudness", "key", "mode"
        ]
        
        # Verify columns exist
        existing_features = [f for f in features if f in df.columns]
        if not existing_features:
            return []

        # 2. Prepare Data
        # Filter tracks that have been analyzed (not all zeros)
        analyzed_mask = (df["energy"] != 0) | (df["danceability"] != 0)
        analyzed_df = df[analyzed_mask].copy()
        
        if len(analyzed_df) < 2:
            return []

        # 3. Normalization (Z-score)
        # We normalize because tempo (~120) and valence (0-1) are on different scales
        scaler = StandardScaler()
        data_normalized = scaler.fit_transform(analyzed_df[existing_features].fillna(0))
        
        # 4. Building User Profile
        if user_profile_tracks is None:
            # Use last 20 tracks from analyzed history
            # Higher weight to more recent tracks (Linear decay)
            recent_data = data_normalized[-20:]
            weights = np.linspace(0.5, 1.0, len(recent_data))
            user_profile = np.average(recent_data, axis=0, weights=weights).reshape(1, -1)
        else:
            # Use provided profile tracks
            profile_data = scaler.transform(user_profile_tracks[existing_features].fillna(0))
            user_profile = np.mean(profile_data, axis=0).reshape(1, -1)
            
        # 5. Compute Similarity
        similarities = cosine_similarity(user_profile, data_normalized).flatten()
        
        # 6. Sort and Filter
        recommended_indices = np.argsort(similarities)[::-1]
        
        # Get top tracks, filtering out duplicates
        recommendations = analyzed_df.iloc[recommended_indices].head(n_recommendations + 20)
        recommendations = recommendations.drop_duplicates(subset=["track_name", "artist"]).head(n_recommendations)
        
        # Cleanup for JSON
        clean_recs = recommendations.replace({np.nan: None}).to_dict(orient="records")
        return clean_recs
