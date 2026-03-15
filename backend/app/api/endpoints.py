import asyncio
import time
import pandas as pd
import numpy as np
import os
import urllib.parse
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
import httpx

from ..services.spotify_service import SpotifyService
from ..services.data_service import DataService
from ..services.recommendation_service import RecommendationService
from ..services.audio_analysis_service import AudioAnalysisService
from ..services.ytmusic_service import YTMusicService
from ..models.schemas import TrackFeatures, SyncStatus
from ..core.logging import Logger

router = APIRouter()

@router.get("/status")
async def get_status():
    """Checks Spotify connection status."""
    sp = SpotifyService()
    return {"connected": sp.is_connected(), "user": sp.user_name}

@router.get("/user-profile")
async def get_user_profile():
    """Returns real Spotify user profile."""
    sp = SpotifyService()
    return sp.get_user_profile()

@router.get("/sync", response_model=SyncStatus)
async def sync_data():
    """Synchronizes user data with extreme resilience."""
    t0 = time.time()
    try:
        sp = SpotifyService()
        if not sp.is_connected():
            Logger.warning("SYNC", "Spotify disconnected. Using cache.")
            df = DataService.load_library()
            return SyncStatus(status="warning", new_tracks=0, total_library=len(df), time_taken="0s (Cached)")
        
        # Parallel fetch if possible, but sequential is safer for rate limits
        all_tracks = sp.get_top_tracks_with_features() + sp.get_recently_played_with_features()
        
        df = DataService.append_new_tracks(all_tracks, user_name=sp.user_name, user_id=sp.user_id)
        elapsed = f"{time.time() - t0:.2f}s"
        return SyncStatus(status="success", new_tracks=len(all_tracks), total_library=len(df), time_taken=elapsed)
    except Exception as e:
        Logger.error("SYNC", f"Sync failed: {e}")
        df = DataService.load_library()
        return SyncStatus(status="partial", new_tracks=0, total_library=len(df), time_taken="N/A")

@router.get("/recommendations", response_model=List[TrackFeatures])
async def get_recommendations(limit: int = 10, mode: str = "vibe", song: Optional[str] = None):
    """Hybrid recommendation engine."""
    sp = SpotifyService()
    lib_df = DataService.load_library()
    user_df = DataService.load_user_data(sp.user_id)
    
    # Discovery mode (Spotify-led)
    if mode == "discovery" and sp.is_connected():
        seed_ids = user_df["spotify_id"].sample(min(5, len(user_df))).tolist() if not user_df.empty else []
        recs = sp.get_recommendations_from_spotify(seed_ids, limit=limit)
        if recs: return recs

    # Vibe mode (Local-led content matching)
    target_profile = None
    if song:
        target_track = await _prepare_target_track(song, sp, lib_df)
        if target_track and "target_features" in target_track and target_track["target_features"]:
            target_profile = pd.DataFrame([target_track["target_features"]])

    if lib_df.empty: 
        raise HTTPException(status_code=404, detail="Library empty.")
        
    return RecommendationService.get_recommendations(lib_df, user_profile_tracks=target_profile if target_profile is not None else user_df, n_recommendations=limit)

async def _prepare_target_track(query: str, sp: SpotifyService, lib_df: pd.DataFrame):
    """Finds and enriches a track for seeds."""
    track = sp.search_track(query)
    if not track: return None
    
    if not lib_df.empty:
        mask = lib_df["spotify_id"] == track["id"]
        if mask.any():
            track["target_features"] = lib_df[mask].iloc[0].to_dict()
    
    if not track.get("target_features"):
        preview = track.get("preview_url") or AudioAnalysisService.get_preview_from_itunes(track["name"], track["artist"])
        if preview:
            track["target_features"] = AudioAnalysisService.analyze_preview(preview)
            
    if track.get("target_features"):
        # Background persistence skipped here for speed, just return it
        pass
    return track

@router.get("/search")
async def search_tracks(query: str, limit: int = 10):
    """Resilient search prioritizing Spotify then YouTube."""
    if not query: return []
    
    sp = SpotifyService()
    if sp.is_connected():
        results = sp._call_api("search", q=query, limit=limit, type="track")
        if results and "tracks" in results and results["tracks"]["items"]:
            return [{
                "id": t["id"],
                "track_name": t["name"],
                "artist": t["artists"][0]["name"],
                "album": t["album"]["name"],
                "thumbnail": t["album"]["images"][0]["url"] if t["album"]["images"] else None,
                "spotify_id": t["id"]
            } for t in results["tracks"]["items"]]
            
    return YTMusicService.search_tracks(query, limit=limit)

@router.get("/stats")
async def get_stats():
    """Optimized stats aggregation."""
    sp = SpotifyService()
    df = DataService.load_user_data(sp.user_id)
    if df.empty: return {"status": "no_data"}
    
    analyzed = df[df["energy"] > 0]
    base = analyzed if not analyzed.empty else df
    
    counts = df["artist"].value_counts()
    top_artist = counts.index[0] if not counts.empty else "N/A"
    
    genre_counts = df[df["genre"] != "Unknown"]["genre"].value_counts().head(10)
    total_known_genres = genre_counts.sum()
    genre_percent = (genre_counts / total_known_genres * 100).round(1).to_dict() if total_known_genres > 0 else {}

    return {
        "total_tracks": len(df),
        "unanalyzed_tracks": len(df[df["energy"] == 0]),
        "avg_popularity": float(base["popularity"].mean()),
        "avg_energy": float(base["energy"].mean()),
        "avg_danceability": float(base["danceability"].mean()),
        "avg_valence": float(base["valence"].mean()),
        "avg_acousticness": float(base["acousticness"].mean()) if "acousticness" in base.columns else 0.0,
        "avg_instrumentalness": float(base["instrumentalness"].mean()) if "instrumentalness" in base.columns else 0.0,
        "avg_tempo": float(base["tempo"].mean()),
        "top_1_artist": top_artist,
        "top_artists": counts.head(10).to_dict(),
        "top_genres": genre_percent,
        "distribution": {
            "energy": base["energy"].head(100).tolist(),
            "danceability": base["danceability"].head(100).tolist()
        }
    }

@router.get("/history")
async def get_history(limit: int = 100):
    """User history with NaN safety."""
    sp = SpotifyService()
    df = DataService.load_user_data(sp.id if hasattr(sp, 'id') else None)
    if df.empty: return []
    # Replace NaN and Inf to avoid JSON errors
    return df.tail(limit).iloc[::-1].replace({np.nan: None, np.inf: 0, -np.inf: 0}).to_dict(orient="records")

# Simple memory cache for resolved streams to avoid yt-dlp overhead
# Key: spotify_id or track_name+artist, Value: (data, expiry)
STREAM_CACHE: Dict[str, tuple] = {}
# Concurrency limit for heavy yt-dlp operations
STREAM_SEMAPHORE = asyncio.Semaphore(3)

@router.get("/stream")
async def get_stream(track: str, artist: str = "", spotify_id: Optional[str] = None):
    """Stream URL resolver with persistent database-first cache and active expiry check."""
    cache_key = spotify_id or f"{track}_{artist}".lower().replace(" ", "")
    now = time.time()
    
    # 1. Check Memory Cache (Fastest)
    if cache_key in STREAM_CACHE:
        data, expiry = STREAM_CACHE[cache_key]
        if now < expiry - 60: # 60s safety buffer
            return data

    # 2. Check Database Cache (Persistent)
    yt_id = None
    if spotify_id:
        lib_item = DataService.get_indexed_library().get(spotify_id)
        if lib_item is not None:
            # Handle both Series and scalar (depending on indexing)
            if isinstance(lib_item, pd.Series):
                yt_id = lib_item.get("yt_id")
                s_url = lib_item.get("stream_url")
                s_exp = lib_item.get("stream_expiry", 0)
            else:
                yt_id = lib_item["yt_id"].iloc[0]
                s_url = lib_item["stream_url"].iloc[0]
                s_exp = lib_item["stream_expiry"].iloc[0]
            
            if pd.isna(yt_id): yt_id = None
            
            # If we have a valid non-expired URL in DB, reuse it!
            if s_url and s_url != "Unknown" and s_exp > now + 300: # 5 min buffer
                res = {
                    "stream_url": s_url,
                    "video_id": yt_id,
                    "title": f"{artist} - {track}",
                    "duration": 0
                }
                STREAM_CACHE[cache_key] = (res, s_exp)
                return res

    # 3. Resolve via API (Blocking)
    async with STREAM_SEMAPHORE:
        res = await asyncio.to_thread(YTMusicService.search_and_get_stream, track, artist, video_id=yt_id)
    
    if not res or not res.get("stream_url"):
        raise HTTPException(404, "Stream not found")
    
    # Extract expiry from YT URL (default 6h if not found)
    expiry = now + 6 * 3600
    try:
        parsed = urllib.parse.urlparse(res["stream_url"])
        qs = urllib.parse.parse_qs(parsed.query)
        if 'expire' in qs:
            expiry = float(qs['expire'][0])
    except: pass

    # 4. Save to Database & Memory Cache
    if spotify_id:
        metadata = {"yt_id": res.get("video_id"), "stream_url": res["stream_url"], "stream_expiry": expiry}
        DataService.update_track_metadata(spotify_id, metadata, track_name=track, artist=artist)
        
    res["stream_url"] = f"http://localhost:8000/api/proxy-audio?url={urllib.parse.quote_plus(res['stream_url'])}"
    STREAM_CACHE[cache_key] = (res, expiry)
    return res

@router.get("/proxy-audio")
async def proxy_audio(url: str, request: Request):
    """Proxies audio with Range support for seeking."""
    headers = {"User-Agent": "Mozilla/5.0"}
    if r := request.headers.get("range"): headers["Range"] = r

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # We use stream=True-like behavior with aiter_bytes
            resp = await client.get(url, headers=headers, follow_redirects=True)
            return StreamingResponse(
                resp.aiter_bytes(),
                status_code=resp.status_code,
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Type": resp.headers.get("Content-Type", "audio/mpeg"),
                    "Content-Range": resp.headers.get("Content-Range", ""),
                    "Content-Length": resp.headers.get("Content-Length", "")
                }
            )
        except Exception as e:
            Logger.error("PROXY", f"Proxy error: {e}")
            return Response(status_code=500)
