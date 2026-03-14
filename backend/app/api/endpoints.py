from fastapi import APIRouter, HTTPException
import pandas as pd
from ..services.spotify_service import SpotifyService
from ..services.data_service import DataService
from ..services.analysis_service import AnalysisService
from ..services.recommendation_service import RecommendationService

router = APIRouter()

import time

@router.get("/sync")
async def sync_data():
    t0 = time.time()
    try:
        print("[SYNC] Starting sync process...")
        spotify = SpotifyService()
        
        t1 = time.time()
        top_tracks = spotify.get_top_tracks_with_features()
        print(f"[SYNC] got top tracks in {time.time()-t1:.3f}s")
        
        t2 = time.time()
        recent_tracks = spotify.get_recently_played_with_features()
        print(f"[SYNC] got recent tracks in {time.time()-t2:.3f}s")
        
        all_new_tracks = top_tracks + recent_tracks
        
        t3 = time.time()
        df = DataService.append_new_tracks(all_new_tracks, user_name=spotify.user_name, user_id=spotify.user_id)
        print(f"[SYNC] appended tracks in {time.time()-t3:.3f}s")
        
        print(f"[SYNC] Total time: {time.time()-t0:.3f}s")
        return {"status": "success", "tracks_synced": len(all_new_tracks), "total_tracks": len(df), "user": spotify.user_name}
    except Exception as e:
        print(f"[SYNC] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis")
async def get_analysis():
    spotify = SpotifyService()
    df = DataService.load_data(user_id=spotify.user_id)
    if df.empty:
        return {"status": "no_data", "message": "No data available. Please sync first."}
    
    stats = AnalysisService.get_summary_stats(df)
    return stats

@router.get("/recommendations")
async def get_recommendations(limit: int = 10, mode: str = "vibe", song: str = None):
    t0 = time.time()
    print(f"[REC] Starting recommendations (mode={mode}, limit={limit}, song={song})...")
    
    t1 = time.time()
    library_df = DataService.load_library()
    print(f"[REC] Loaded library in {time.time()-t1:.3f}s (len={len(library_df)})")
    
    spotify = SpotifyService()
    user_df = DataService.load_data(user_id=spotify.user_id) # Returns joined view
    
    if not spotify.is_connected():
        raise HTTPException(status_code=503, detail="Spotify disconnected")

    # If song is specified, we find recommendations based AT LEAST on that song
    target_track = None
    if song:
        t2 = time.time()
        target_track = spotify.search_track(song)
        print(f"[REC] Searched track in {time.time()-t2:.3f}s")
        if not target_track:
            raise HTTPException(status_code=404, detail="Song not found")
            
        # Enrich target_track with features if available locally, already in search, or from analysis
        local_match = library_df[library_df["spotify_id"] == target_track["id"]]
        if not local_match.empty:
            target_track["target_features"] = local_match.iloc[0].to_dict()
        elif target_track.get("target_features"):
            # Already have them from Spotify search
            pass
        else:
            # Fallback to direct analysis if not in library or search features failed
            from ..services.audio_analysis_service import AudioAnalysisService
            t3 = time.time()
            preview = target_track.get("preview_url") or AudioAnalysisService.get_preview_from_itunes(target_track["name"], target_track["artist"])
            if preview:
                target_track["target_features"] = AudioAnalysisService.analyze_preview(preview)
            print(f"[REC] Audio analysis took {time.time()-t3:.3f}s")

        # Persistence: If we have features (from Spotify OR analysis), save to library
        if target_track.get("target_features"):
            save_data = {**target_track, **target_track["target_features"]}
            DataService.persist_track(save_data)

    # 1. DISCOVERY MODE (Spotify-led)
    if mode == "discovery":
        t4 = time.time()
        user_taste_ids = user_df["spotify_id"].tail(10).tolist() if not user_df.empty else []
        
        if target_track:
            res = spotify.get_recommendations_weighted(target_track, user_taste_ids, limit=limit)
            print(f"[REC] Spotify weighted recs took {time.time()-t4:.3f}s")
            return res
        else:
            # Random seed from taste
            seed_ids = user_df["spotify_id"].sample(min(5, len(user_df))).tolist() if not user_df.empty else []
            res = spotify.get_recommendations_from_spotify(seed_ids, limit=limit)
            print(f"[REC] Spotify standard recs took {time.time()-t4:.3f}s")
            return res

    # 2. VIBE MODE (Local Library matching)
    if mode == "vibe":
        t5 = time.time()
        if library_df.empty:
            return {"status": "no_data", "message": "Library is empty."}
            
        # If we have a target track, recommend similar to it
        if target_track and "target_features" in target_track:
            # We wrap target features in a mock DF for RecommendationService
            target_df = pd.DataFrame([target_track["target_features"]])
            res = RecommendationService.get_recommendations(library_df, user_profile_tracks=target_df, n_recommendations=limit)
            print(f"[REC] Vibe recs (with target) took {time.time()-t5:.3f}s")
            return res
        
        # Default: recommend based on recent history
        res = RecommendationService.get_recommendations(library_df, user_profile_tracks=None, n_recommendations=limit)
        print(f"[REC] Vibe recs (no target) took {time.time()-t5:.3f}s")
        return res

    return {"error": "Invalid mode. Use 'vibe' or 'discovery'"}

@router.get("/similar-tracks")
async def get_similar_tracks(track_id: str, limit: int = 5):
    """Finds similar tracks in local library for a given ID."""
    library_df = DataService.load_library()
    match = library_df[library_df["spotify_id"] == track_id]
    
    if match.empty:
        raise HTTPException(status_code=404, detail="Track not in local records")
        
    return RecommendationService.get_recommendations(library_df, user_profile_tracks=match, n_recommendations=limit)

@router.get("/analyze-track")
async def analyze_track(song: str, artist: str = ""):
    spotify = SpotifyService()
    if not spotify.is_connected():
        raise HTTPException(status_code=503, detail="Spotify disconnected")

    # 1. Search for track to get preview_url
    query = f"{song} {artist}"
    track = spotify.search_track(query)
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    from ..services.audio_analysis_service import AudioAnalysisService
    preview_url = track.get("preview_url")
    
    # Si Spotify no tiene preview, intentamos iTunes
    if not preview_url:
        print(f"Spotify preview missing for {track['name']}, trying iTunes...")
        preview_url = AudioAnalysisService.get_preview_from_itunes(track["name"], track["artist"])

    if not preview_url:
        return {
            "error": "No preview available for this track on Spotify or iTunes.",
            "suggestions": [f"Try searching for a different version of {song}", "Check if the song is available in your region"]
        }

    # 2. Analyze audio
    analysis = AudioAnalysisService.analyze_preview(preview_url)

    if not analysis:
        raise HTTPException(status_code=500, detail="Could not analyze audio preview")

    # Persistence: Save the analyzed track to library
    full_track_data = {
        "track_name": track["name"],
        "artist": track["artist"],
        "spotify_id": track["id"],
        "artist_id": track.get("artist_id"),
        **analysis
    }
    DataService.persist_track(full_track_data)

    return full_track_data

@router.get("/user-profile")
async def get_user_profile():
    spotify = SpotifyService()
    df = DataService.load_data(user_id=spotify.user_id)
    if df.empty:
        return {"status": "no_data", "message": "No data available. Please sync first."}
    
    features = ["danceability", "energy", "tempo", "valence", "popularity"]
    # Ensure numeric
    temp_df = df.copy()
    for f in features:
        if f in temp_df.columns:
            temp_df[f] = pd.to_numeric(temp_df[f], errors='coerce').fillna(0)
            
    profile = temp_df[features].mean().to_dict()
    
    return {
        "user_features": profile,
        "total_tracks_analyzed": len(df)
    }
