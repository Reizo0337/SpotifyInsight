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
    def get_recommendations(cls, history_tracks, candidates, n_recommendations=10, spotify_recs=None):
        """Generates hybrid recommendations using SQL models as input."""
        start_time = time.time()
        
        if not history_tracks and not spotify_recs:
            return candidates[:n_recommendations]
            
        # 1. Convert models to DataFrame for vector operations
        def tracks_to_df(tracks):
            data = []
            for t in tracks:
                d = {f: getattr(t, f, 0.0) or 0.0 for f in cls.FEATURES}
                d["spotify_id"] = t.spotify_id
                d["track_name"] = t.track_name
                d["artist"] = t.artist
                d["album"] = getattr(t, "album", "Unknown")
                d["thumbnail"] = getattr(t, "thumbnail", "")
                d["duration_ms"] = getattr(t, "duration_ms", 0)
                d["yt_id"] = getattr(t, "yt_id", None)
                d["stream_url"] = getattr(t, "stream_url", None)
                data.append(d)
            return pd.DataFrame(data)

        # 2. Build User Profile from history
        if history_tracks:
            history_df = tracks_to_df(history_tracks)
            X_hist = cls._prepare_feature_matrix(history_df)
            user_profile = np.mean(X_hist, axis=0).reshape(1, -1)
        else:
            # If no history, use spotify_recs as profile base
            user_profile = np.zeros((1, len(cls.FEATURES)))

        # 3. Score Candidates
        candidate_df = tracks_to_df(candidates)
        X_cand = cls._prepare_feature_matrix(candidate_df)
        
        similarities = cosine_similarity(user_profile, X_cand).flatten()
        
        # 4. Rank and combine
        candidate_df["score"] = similarities
        top_local = candidate_df.sort_values("score", ascending=False).head(n_recommendations)
        
        # Convert back to dicts
        local_results = top_local.to_dict("records")
        
        # Merge with spotify_recs if available
        if spotify_recs:
            # Very simple merge: mix them, prioritizing variety
            seen = set()
            final = []
            for i in range(max(len(local_results), len(spotify_recs))):
                if i < len(local_results):
                    track = local_results[i]
                    if track["spotify_id"] not in seen:
                        final.append(track)
                        seen.add(track["spotify_id"])
                if i < len(spotify_recs):
                    track = spotify_recs[i]
                    sid = track.get("id") or track.get("spotify_id")
                    if sid not in seen:
                        final.append(track)
                        seen.add(sid)
                if len(final) >= n_recommendations: break
            return final[:n_recommendations]
            
        return local_results

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
