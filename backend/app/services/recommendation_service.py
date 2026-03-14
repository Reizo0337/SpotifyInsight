from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

class RecommendationService:
    _cached_matrix = None
    _cached_df_len = 0
    _cached_features = None

    @staticmethod
    def get_recommendations(df, user_profile_tracks=None, n_recommendations=10):
        import time
        start_time = time.time()
        
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

        # 2. Prepare Data & Filtering
        t1 = time.time()
        # If library is too huge, we sample to keep the API responsive
        if len(df) > 500000:
            # We keep recent tracks always, then sample the rest
            recent_count = 10000
            sampled_df = pd.concat([df.tail(recent_count), df.head(len(df)-recent_count).sample(n=490000)])
        else:
            sampled_df = df

        analyzed_mask = (sampled_df["energy"] != 0) | (sampled_df["danceability"] != 0)
        analyzed_df = sampled_df[analyzed_mask].copy()
        print(f"[REC] Data preparation took {time.time()-t1:.3f}s (analyzed tracks: {len(analyzed_df)})")
        
        if len(analyzed_df) < 2:
            return []

        # 3. Optimized Similarity Calculation
        # Instead of fit_transform every time (O(N)), we do a simpler min-max or just raw with weights
        # For tempo, we divide by 200 to scale it 0-1 approx
        X = analyzed_df[existing_features].fillna(0).values.copy()
        
        # Simple normalization to avoid full scaler cost
        # danceability, energy, valence, acousticness, instrumentalness, speechiness are already 0-1
        # tempo(idx 2), loudness(idx 7), key(idx 8) need scaling
        tempo_idx = existing_features.index("tempo") if "tempo" in existing_features else -1
        loudness_idx = existing_features.index("loudness") if "loudness" in existing_features else -1
        
        if tempo_idx != -1: X[:, tempo_idx] /= 200.0
        if loudness_idx != -1: X[:, loudness_idx] = (X[:, loudness_idx] + 60) / 60.0
        
        # 4. Building User Profile
        t3 = time.time()
        if user_profile_tracks is None:
            # Use last 50 tracks
            recent_indices = np.arange(max(0, len(X)-50), len(X))
            weights = np.linspace(0.5, 1.0, len(recent_indices))
            user_profile = np.average(X[recent_indices], axis=0, weights=weights).reshape(1, -1)
        else:
            profile_x = user_profile_tracks[existing_features].fillna(0).values.copy()
            if tempo_idx != -1: profile_x[:, tempo_idx] /= 200.0
            if loudness_idx != -1: profile_x[:, loudness_idx] = (profile_x[:, loudness_idx] + 60) / 60.0
            user_profile = np.mean(profile_x, axis=0).reshape(1, -1)
        print(f"[REC] Profile building took {time.time()-t3:.3f}s")
            
        # 5. Compute Similarity (O(N) but very fast in NumPy)
        t4 = time.time()
        similarities = cosine_similarity(user_profile, X).flatten()
        print(f"[REC] Similarity computation took {time.time()-t4:.3f}s")
        
        # 6. Sort and Filter
        t5 = time.time()
        recommended_indices = np.argsort(similarities)[::-1]
        
        # Get top tracks, filtering out duplicates
        recommendations = analyzed_df.iloc[recommended_indices].head(n_recommendations + 20)
        recommendations = recommendations.drop_duplicates(subset=["track_name", "artist"]).head(n_recommendations)
        
        # Cleanup for JSON
        clean_recs = recommendations.replace({np.nan: None}).to_dict(orient="records")
        print(f"[REC] Sorting and cleanup took {time.time()-t5:.3f}s")
        print(f"[REC] TOTAL processing time: {time.time()-start_time:.3f}s")
        return clean_recs
        
