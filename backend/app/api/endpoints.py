import time
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse, FileResponse
import numpy as np
import os
import json
import httpx
import urllib.parse
from typing import List, Optional

from ..services.spotify_service import SpotifyService
from ..services.data_service import DataService
from ..services.recommendation_service import RecommendationService
from ..services.audio_analysis_service import AudioAnalysisService
from ..services.ytmusic_service import YTMusicService
from ..models.schemas import TrackFeatures, SyncStatus, RecommendationRequest
from ..core.logging import Logger

router = APIRouter()

@router.get("/sync", response_model=SyncStatus)
async def sync_data():
    """
    Synchronizes user data with extreme resilience.
    If Spotify is rate-limited, it returns current library status instead of failing.
    """
    t0 = time.time()
    Logger.info("SYNC", "Starting synchronization...")
    
    try:
        spotify = SpotifyService()
        
        # If we are strictly blocked, we don't even try Spotify, just return current library.
        if not spotify.is_connected():
            Logger.warning("SYNC", "Spotify is currently rate-limited or disconnected. Returning cached library.")
            df = DataService.load_library()
            return SyncStatus(
                status="warning",
                new_tracks=0,
                total_library=len(df),
                time_taken="0s (Cached)"
            )
        
        # 1. Fetch data from Spotify
        top = spotify.get_top_tracks_with_features()
        recent = spotify.get_recently_played_with_features()
        all_tracks = top + recent
        
        if not all_tracks:
            # Maybe everything was already cached or we got a soft 429
            df = DataService.load_library()
            return SyncStatus(
                status="success",
                new_tracks=0,
                total_library=len(df),
                time_taken=f"{time.time() - t0:.2f}s"
            )

        # 2. Update local storage
        df = DataService.append_new_tracks(
            all_tracks, 
            user_name=spotify.user_name, 
            user_id=spotify.user_id
        )
        
        elapsed = f"{time.time() - t0:.2f}s"
        Logger.success("SYNC", f"Synchronized {len(all_tracks)} tracks in {elapsed}")
        
        return SyncStatus(
            status="success",
            new_tracks=len(all_tracks),
            total_library=len(df),
            time_taken=elapsed
        )
    except Exception as e:
        Logger.error("SYNC", f"Process encountered an issue: {e}")
        # Final fallback: just return what we have
        df = DataService.load_library()
        return SyncStatus(
            status="partial",
            new_tracks=0,
            total_library=len(df),
            time_taken="N/A"
        )

@router.get("/recommendations", response_model=List[TrackFeatures])
async def get_recommendations(
    limit: int = 10, 
    mode: str = "vibe", 
    song: Optional[str] = None
):
    """
    Hybrid recommendation engine.
    - vibe: Content-based matching against local library.
    - discovery: Spotify-led recommendations weighted by user taste.
    """
    t_start = time.time()
    Logger.info("REC", f"Generating {limit} recs (mode={mode}, query={song})")
    
    spotify = SpotifyService()
    lib_df = DataService.load_library()
    user_df = DataService.load_user_data(spotify.user_id)
    Logger.info("API", f"Recs requested: Lib size={len(lib_df)}, User history size={len(user_df)}")
    
    target_track = None
    if song:
        target_track = await _prepare_target_track(song, spotify, lib_df)

    # Mode 1: Discovery (External)
    if mode == "discovery":
        seed_ids = user_df["spotify_id"].sample(min(5, len(user_df))).tolist() if not user_df.empty else []
        recs = spotify.get_recommendations_from_spotify(seed_ids, limit=limit)
        
        if recs:
            return recs
        else:
            Logger.info("REC", "Spotify discovery failed (403?), falling back to Vibe engine.")
            # Fallback to internal vibe engine
            return RecommendationService.get_recommendations(lib_df, user_profile_tracks=user_df, n_recommendations=limit)

    # Mode 2: Vibe (Internal)
    if mode == "vibe":
        if lib_df.empty: 
            raise HTTPException(status_code=404, detail="Empty library. Please sync first.")
            
        target_profile = pd.DataFrame([target_track["target_features"]]) if target_track and "target_features" in target_track else None
        return RecommendationService.get_recommendations(lib_df, user_profile_tracks=target_profile, n_recommendations=limit)

    raise HTTPException(status_code=400, detail="Invalid recommendation mode")

async def _prepare_target_track(query: str, spotify: SpotifyService, lib_df: pd.DataFrame):
    """Helper to find and enrich a target track for recommendations."""
    track = spotify.search_track(query)
    if not track:
        raise HTTPException(status_code=404, detail="Song not found")
        
    # Enrich features: Local -> Search -> Analysis
    local_match = lib_df[lib_df["spotify_id"] == track["id"]]
    if not local_match.empty:
        track["target_features"] = local_match.iloc[0].to_dict()
    elif not track.get("target_features"):
        preview = track.get("preview_url") or AudioAnalysisService.get_preview_from_itunes(track["name"], track["artist"])
        if preview:
            track["target_features"] = AudioAnalysisService.analyze_preview(preview)
            
    # Persist if enriched
    if track.get("target_features"):
        DataService.save_library(pd.concat([lib_df, pd.DataFrame([{**track, **track["target_features"]}])]))
        
    return track

@router.get("/search")
async def search_tracks(query: str, limit: int = 10):
    """
    Search endpoint with extreme resilience.
    Prioritizes YouTube if Spotify is flagged as blocked.
    """
    if not query:
        return []
    
    try:
        final_results = []
        spotify = SpotifyService()
        
        # 1. TRY Spotify First
        if spotify.is_connected() and "search" not in spotify._forbidden_endpoints:
            Logger.info("API", f"Searching Spotify for '{query}'")
            results = spotify._call_api("search", q=query, limit=limit, type="track")
            if results and "tracks" in results and results["tracks"]["items"]:
                tracks = results["tracks"]["items"]
                final_results = [{
                    "id": t["id"],
                    "track_name": t["name"],
                    "artist": t["artists"][0]["name"],
                    "album": t["album"]["name"],
                    "thumbnail": t["album"]["images"][0]["url"] if t["album"]["images"] else None,
                    "spotify_id": t["id"]
                } for t in tracks]

        # 2. FALLBACK to YouTube if Spotify fails or yields no results
        if not final_results:
            Logger.info("API", f"Spotify unavailable or no results. Falling back to YouTube for '{query}'")
            yt_results = YTMusicService.search_tracks(query, limit=limit)
            if yt_results:
                final_results = yt_results
        
        return final_results
    except Exception as e:
        Logger.error("API", f"Critical failure in /search: {e}")
        return []

@router.get("/stats")
async def get_stats():
    """Provides high-level statistics about the local music library."""
    try:
        spotify = SpotifyService()
        df = DataService.load_user_data(spotify.user_id)
        if df.empty:
            return {"status": "no_data", "message": "Library is empty."}
        
        analyzed_df = df[df["energy"] > 0]
        
        # If no analyzed tracks, use full df but averages will be 0. 
        # Better to show 0 only if truly checked.
        stats_df = analyzed_df if not analyzed_df.empty else df
        
        top_artist_name = df["artist"].value_counts().index[0] if not df.empty else "N/A"
        top_track_row = df.sort_values("popularity", ascending=False).iloc[0] if not df.empty else None
        
        import numpy as np
        
        def sanitize(val):
            if isinstance(val, (np.float32, np.float64)): return float(val)
            if isinstance(val, (np.int32, np.int64)): return int(val)
            return val

        res = {
            "total_tracks": int(len(df)),
            "unanalyzed_tracks": int(len(df[df["energy"] == 0])),
            "avg_popularity": float(stats_df["popularity"].mean()),
            "avg_energy": float(stats_df["energy"].mean()),
            "avg_danceability": float(stats_df["danceability"].mean()),
            "avg_valence": float(stats_df["valence"].mean()),
            "avg_tempo": float(stats_df["tempo"].mean()),
            "top_1_artist": str(top_artist_name),
            "top_1_track": str(top_track_row["track_name"]) if top_track_row is not None else "N/A",
            "top_artists": {str(k): int(v) for k, v in df["artist"].value_counts().head(10).to_dict().items()},
            "top_genres": {str(k): int(v) for k, v in df[df["genre"] != "Unknown"]["genre"].value_counts().head(5).to_dict().items()},
            "distribution": {
                "energy": [float(x) for x in stats_df["energy"].tolist()[:100]],
                "danceability": [float(x) for x in stats_df["danceability"].tolist()[:100]]
            }
        }
        return res
    except Exception as e:
        import traceback
        Logger.error("API", f"Stats failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_history(limit: int = 100):
    """Returns the user's recent listening history."""
    try:
        spotify = SpotifyService()
        df = DataService.load_user_data(spotify.user_id)
        
        if df.empty:
            Logger.info("API", "History requested but history is empty.")
            return []
            
        import numpy as np
        # Return last N tracks, reversed to show newest first
        history_df = df.tail(limit).iloc[::-1]
        history = history_df.replace({np.nan: None}).to_dict(orient="records")
        return history
    except Exception as e:
        import traceback
        Logger.error("API", f"History failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-profile")
async def get_user_profile():
    """Returns an aggregated profile of user musical tastes."""
    spotify = SpotifyService()
    df = DataService.load_user_data(spotify.user_id)
    if df.empty:
        return {"status": "no_data", "message": "No data. Sync first."}
    
    cols = ["danceability", "energy", "tempo", "valence", "popularity"]
    profile = df[cols].mean().to_dict()
    
    return {
        "user_name": spotify.user_name,
        "features": profile,
        "total_tracks": len(df)
    }

@router.get("/analyze-track", response_model=TrackFeatures)
async def analyze_track(song: str, artist: str = ""):
    """Performs deep audio analysis on a specific track."""
    spotify = SpotifyService()
    track = spotify.search_track(f"{song} {artist}")
    if not track: raise HTTPException(status_code=404, detail="Track not found")

    preview = track.get("preview_url") or AudioAnalysisService.get_preview_from_itunes(track["name"], track["artist"])
    if not preview: raise HTTPException(status_code=400, detail="No audio preview available")

    analysis = AudioAnalysisService.analyze_preview(preview)
    if not analysis: raise HTTPException(status_code=500, detail="Analysis failed")

    full_data = {
        "spotify_id": track["id"],
        "track_name": track["name"],
        "artist": track["artist"],
        **analysis
    }
    # Save to library for future use
    DataService.append_new_tracks([full_data], user_id=spotify.user_id)
    

@router.get("/stream")
async def get_stream_url(track: str, artist: str = ""):
    """
    Searches YouTube Music for 'artist - track' and returns a
    URL to our LOCAL proxy, which handles the actual streaming.
    """
    if not track:
        raise HTTPException(status_code=400, detail="track parameter is required")
    
    Logger.info("STREAM", f"Stream requested: {artist} - {track}")
    result = YTMusicService.search_and_get_stream(track_name=track, artist=artist)
    
    if not result or not result.get("stream_url"):
        raise HTTPException(
            status_code=404,
            detail=f"Could not find a playable stream for '{artist} - {track}'."
        )
    
    # Instead of returning the direct Google URL (which has CORS issues),
    # we return a link to our own proxy endpoint.
    # Construct proxy URL — we encode the stream_url to pass it safely
    encoded_url = urllib.parse.quote_plus(result["stream_url"])
    
    # We return the same metadata but with a proxied URL
    result["stream_url"] = f"http://localhost:8000/api/proxy-audio?url={encoded_url}"
    return result

@router.get("/proxy-audio")
async def proxy_audio(url: str, request: Request):
    """
    Proxies audio from YouTube/Google Video with Range support for seeking.
    """
    # We need to handle Range requests from the browser for seeking
    range_header = request.headers.get("range")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    if range_header:
        headers["Range"] = range_header

    try:
        # Using a timeout and follow_redirects for YouTube URLs
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, follow_redirects=True, timeout=15)
            
            # Forward relevant headers back to the browser
            response_headers = {
                "Accept-Ranges": "bytes",
                "Content-Type": resp.headers.get("Content-Type", "audio/mpeg"),
            }
            if resp.headers.get("Content-Range"):
                response_headers["Content-Range"] = resp.headers.get("Content-Range")
            if resp.headers.get("Content-Length"):
                response_headers["Content-Length"] = resp.headers.get("Content-Length")

            return StreamingResponse(
                resp.aiter_bytes(),
                status_code=resp.status_code,
                headers=response_headers
            )
            
    except Exception as e:
        Logger.error("PROXY", f"Stream proxy error: {e}")
        return Response(status_code=500)
