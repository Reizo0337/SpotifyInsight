from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
import time
import asyncio
import urllib.parse
import httpx
from fastapi.responses import StreamingResponse
import json
import uuid

from ..db.session import get_db
from ..db.models import Track, History, User, Favorite
from ..core.auth_utils import get_current_user
from ..services.spotify_service import SpotifyService
from ..services.ytmusic_service import YTMusicService
from ..services.recommendation_service import RecommendationService
from ..core.logging import Logger
from ..schemas import TrackBase, TrackFeatures, SyncStatus

router = APIRouter()

def nebulize_track(t: any):
    """Wraps a database track object OR dict with security-cleared signals and metadata."""
    if not t: return None
    
    # Extract raw data
    if hasattr(t, "spotify_id"): # SQL Model
        sid = t.spotify_id
        name = t.track_name
        artist = t.artist or "Unknown"
        album = t.album or "Unknown"
        thumb = t.thumbnail or ""
        duration = t.duration_ms or 0
        pop = t.popularity or 0
        yid = t.yt_id
        s_url = t.stream_url
        expired = (t.stream_expiry and t.stream_expiry < time.time() + 120)
    else: # Dictionary
        sid = t.get("spotify_id") or t.get("id")
        name = t.get("track_name") or t.get("name", "Unknown")
        artist = t.get("artist") or "Unknown"
        album = t.get("album") or "Unknown"
        thumb = t.get("thumbnail") or ""
        duration = t.get("duration_ms") or t.get("duration", 0)
        pop = t.get("popularity", 0)
        yid = t.get("yt_id")
        s_url = t.get("stream_url")
        expired = False # Dicts from search are usually fresh or empty

    stream = None
    if s_url and not expired:
        # Only proxy if it looks like a direct URL (contains googlevideo or starts with http)
        if s_url.startswith("http") and "proxy_stream" not in s_url:
            quoted_url = urllib.parse.quote(s_url)
            stream = f"http://localhost:8000/api/v1/music/proxy_stream?url={quoted_url}"
        else:
            stream = s_url
        
    return {
        "spotify_id": sid,
        "track_name": name,
        "artist": artist,
        "album": album,
        "thumbnail": thumb,
        "duration_ms": duration,
        "popularity": pop,
        "yt_id": yid,
        "stream_url": stream,
    }

@router.get("/tracks")
async def get_tracks_by_ids(ids: str, db: Session = Depends(get_db)):
    """Fetch track details for multiple IDs from the SQL database."""
    if not ids: return []
    id_list = [id.strip() for id in ids.split(",") if id.strip()]
    
    found = db.query(Track).filter(Track.spotify_id.in_(id_list)).all()
    track_map = {t.spotify_id: t for t in found}
    # Maintain the order of IDs in the input list
    results = []
    for sid in id_list:
        if sid in track_map:
            results.append(nebulize_track(track_map[sid]))
    return results

@router.get("/search")
async def search_tracks(q: str, current_user: User = Depends(get_current_user)):
    """Unified search: Extremely fast metadata retrieval. Prioritizes Spotify for speed."""
    loop = asyncio.get_event_loop()
    
    # Fast path: Spotify API (approx 100-300ms)
    if current_user.spotify_token_info:
        sp = SpotifyService(token_info=current_user.spotify_token_info)
        sp_results = await loop.run_in_executor(None, sp.search_tracks, q, 20)
        if sp_results:
            return [{
                "spotify_id": t["id"],
                "track_name": t["name"],
                "artist": t.get("artists", [{}])[0].get("name", "Unknown"),
                "album": t.get("album", {}).get("name", "Unknown"),
                "thumbnail": t.get("album", {}).get("images", [{}])[0].get("url", ""),
                "duration_ms": t.get("duration_ms", 0),
                "popularity": t.get("popularity", 0)
            } for t in sp_results]

    # Slow path: YTMusic/yt-dlp fallback (approx 1-3s)
    results = await loop.run_in_executor(None, YTMusicService.search_tracks, q, 20)
    # Ensure consistency with field names
    for r in results:
        if "id" in r and "spotify_id" not in r:
            r["spotify_id"] = r["id"]
        if "duration" in r and "duration_ms" not in r:
            r["duration_ms"] = r["duration"] * 1000
    return results

@router.post("/played")
async def log_track_play(spotify_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logs a play event in the history table."""
    # Ensure the track exists in the tracks table (FK requirement)
    exists = db.query(Track).filter(Track.spotify_id == spotify_id).first()
    if not exists:
        Logger.warning("DATABASE", f"Signal {spotify_id} is transient. Skipping history to preserve integrity.")
        return {"status": "success", "info": "transient_signal"}

    new_event = History(user_id=current_user.id, spotify_id=spotify_id)
    db.add(new_event)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        Logger.error("DATABASE", f"Relay log failed: {str(e)}")
        return {"status": "error", "detail": "integrity_violation"}
    return {"status": "success"}

@router.get("/history")
async def get_history(limit: int = 50, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logs of user's celestial journey."""
    history = db.query(Track).join(History).filter(History.user_id == current_user.id).order_by(History.played_at.desc()).limit(limit).all()
    return [nebulize_track(t) for t in history]

@router.get("/spotify/playlists")
async def get_spotify_playlists(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetches the user's remote playlists from Spotify's frequency space."""
    if not current_user.spotify_token_info:
        return []
    
    sp = SpotifyService(token_info=current_user.spotify_token_info)
    
    # Update token if it was refreshed during init
    if sp.updated_token_info and sp.updated_token_info != current_user.spotify_token_info:
        current_user.spotify_token_info = sp.updated_token_info
        db.commit()
        
    if not sp.is_connected():
        Logger.error("SPOTIFY", "Session expired or invalid for playlist fetch")
        return []
        
    return sp.get_user_playlists()

@router.post("/onboarding/complete")
async def complete_onboarding(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Marks the user's initial setup as finalized."""
    prefs = dict(current_user.preferences or {})
    prefs["onboarding_done"] = True
    current_user.preferences = prefs
    db.commit()
    return {"status": "Nebula onboarding finalized"}

@router.post("/onboarding/reset")
async def reset_onboarding(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Resets the user's onboarding status."""
    prefs = dict(current_user.preferences or {})
    prefs["onboarding_done"] = False
    current_user.preferences = prefs
    db.commit()
    return {"status": "Nebula onboarding reset"}

@router.get("/stats")
    total_tracks = db.query(Track).count()
    
    # Defaults if no history
    if not q or q.total_listened == 0:
        return {
            "total_tracks": total_tracks,
            "total_listened": 0,
            "total_playtime_min": 0,
            "avg_energy": 0, "avg_danceability": 0, "avg_valence": 0,
            "avg_tempo": 0, "vibe_intensity": 0, "engagement_score": 0,
            "top_genres": []
        }

    # 2. Composition Metrics
    avg_energy = float(q.avg_energy or 0)
    avg_tempo = float(q.avg_tempo or 0)
    
    # Intensity: Weighted average of energy and normalized tempo (0-1.0)
    vibe_intensity = (avg_energy * 0.7) + ((min(avg_tempo, 180) / 180) * 0.3)
    
    # Engagement: Ratio of diversity vs depth
    engagement_score = min(100, (q.total_listened / max(total_tracks, 1)) * 100)
    
    # 3. Quick Genre Check (Cached or simplified)
    top_genres = []
    # Optionally pull from user preferences if enrichment has happened
    if current_user.preferences and "top_genres" in current_user.preferences:
        top_genres = current_user.preferences["top_genres"]

    return {
        "total_tracks": total_tracks,
        "total_listened": q.total_listened,
        "total_playtime_min": int((q.total_ms or 0) / 60000),
        "avg_energy": avg_energy,
        "avg_danceability": float(q.avg_danceability or 0),
        "avg_valence": float(q.avg_valence or 0),
        "avg_tempo": avg_tempo,
        "avg_popularity": float(q.avg_popularity or 0),
        "vibe_intensity": vibe_intensity,
        "engagement_score": engagement_score,
        "top_genres": top_genres
    }

@router.get("/top/artists")
async def get_top_artists(limit: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Hybrid aggregation of local plays and Spotify's global top."""
    loop = asyncio.get_event_loop()
    # 1. Local data
    local_res = db.query(
        Track.artist, 
        func.count(History.id).label("count"),
        func.max(Track.thumbnail).label("thumbnail")
    ).join(History).filter(History.user_id == current_user.id)\
     .group_by(Track.artist)\
     .order_by(func.count(History.id).desc())\
     .limit(limit).all()
    
    local_map = {r[0]: {"artist": r[0], "play_count": r[1], "thumbnail": r[2], "source": "local"} for r in local_res}
    
    # 2. Spotify data (Non-blocking)
    if current_user.spotify_token_info:
        sp = SpotifyService(token_info=current_user.spotify_token_info)
        sp_art = await loop.run_in_executor(None, sp.get_user_top_artists, limit)
        if sp_art:
            for a in sp_art:
                name = a["name"]
                if name in local_map:
                    local_map[name]["play_count"] += 10 # Boost Spotify tops
                    local_map[name]["source"] = "hybrid"
                else:
                    local_map[name] = {
                        "artist": name,
                        "play_count": 5, # Baseline weight for Spotify top
                        "thumbnail": a["thumbnail"],
                        "source": "spotify"
                    }

    # Sort merged
    merged = sorted(local_map.values(), key=lambda x: x["play_count"], reverse=True)
    return merged[:limit]

@router.get("/top/tracks")
async def get_top_tracks(limit: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Hybrid rank of most resonant tracks."""
    loop = asyncio.get_event_loop()
    # 1. Local
    local_res = db.query(
        Track, 
        func.count(History.id).label("count")
    ).join(History).filter(History.user_id == current_user.id)\
     .group_by(Track.spotify_id)\
     .order_by(func.count(History.id).desc())\
     .limit(limit).all()
    
    results_map = {}
    for t, count in local_res:
        results_map[t.spotify_id] = {
            "track_name": t.track_name,
            "artist": t.artist,
            "thumbnail": t.thumbnail,
            "play_count": count,
            "source": "local"
        }

    # 2. Spotify
    if current_user.spotify_token_info:
        sp = SpotifyService(token_info=current_user.spotify_token_info)
        sp_tracks = await loop.run_in_executor(None, sp.get_user_top_tracks, limit)
        if sp_tracks:
            for t in sp_tracks:
                sid = t["spotify_id"]
                if sid in results_map:
                    results_map[sid]["play_count"] += 5
                    results_map[sid]["source"] = "hybrid"
                else:
                    results_map[sid] = {
                        "spotify_id": sid,
                        "track_name": t["track_name"],
                        "artist": t["artist"],
                        "album": t.get("album", "Unknown"),
                        "thumbnail": t["thumbnail"],
                        "duration_ms": t.get("duration_ms", 0),
                        "play_count": 2,
                        "source": "spotify"
                    }

    merged = sorted(results_map.values(), key=lambda x: x["play_count"], reverse=True)
    return [nebulize_track(t) for t in merged[:limit]]

@router.get("/status")
async def get_status(current_user: User = Depends(get_current_user)):
    """Checks the core system connection levels with zero-latency signal checks."""
    
    # Use cached name from database/preferences
    user_name = current_user.username
    if current_user.preferences and "display_name" in current_user.preferences:
        user_name = current_user.preferences["display_name"]

    return {
        "connected": current_user.spotify_token_info is not None,
        "user_name": user_name,
        "engine": "Nebula Core 2.2 (Ultra-Low Latency)",
        "latency": "Direct SQL Path"
    }

@router.get("/recommendations")
async def get_recommendations(limit: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    ULTRA-LIGHT TRIGGER: Delegates AI analysis to the worker.
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    from ..db.models import Job
    new_job = Job(
        id=job_id,
        user_id=current_user.id,
        type="recommendations",
        status="queued",
        message="Consultando al oráculo musical (IA)...",
        result={"limit": limit}
    )
    db.add(new_job)
    db.commit()

    # Fire Worker
    try:
        import subprocess, sys
        subprocess.Popen([sys.executable, "-m", "app.worker"], start_new_session=True)
    except: pass

    return {"job_id": job_id, "status": "queued"}

@router.get("/proxy_stream")
async def proxy_stream(request: Request, url: str):
    """Pipes an external stream with support for Range requests (Essential for seeking)."""
    range_header = request.headers.get("Range")
    
    # User-Agent strictly required for some signals
    client_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    }
    if range_header:
        client_headers["Range"] = range_header

    try:
        # Establish connection using a persistent client for the generator
        async def stream_generator():
            async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
                async with client.stream("GET", url, headers=client_headers) as r:
                    if r.status_code >= 400:
                        Logger.error("API", f"Upstream signal rejected with status: {r.status_code}")
                        return 
                    
                    async for chunk in r.aiter_bytes(chunk_size=16384):
                        yield chunk

        # Get initial headers to inform the browser (Content-Length and MIME type are crucial)
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as h_client:
            async with h_client.stream("GET", url, headers=client_headers) as h_r:
                if h_r.status_code >= 400:
                    Logger.error("API", f"Upstream signal initialization failed: {h_r.status_code}")
                    raise HTTPException(status_code=h_r.status_code, detail="Fuente de audio protegida o no disponible")
                
                detected_mime = h_r.headers.get("Content-Type", "audio/mpeg")
                res_headers = {
                    "Content-Type": detected_mime,
                    "Accept-Ranges": "bytes",
                    "Content-Length": h_r.headers.get("Content-Length"),
                    "Content-Range": h_r.headers.get("Content-Range"),
                    "Cache-Control": "public, max-age=3600"
                }
                status_code = h_r.status_code if not range_header else 206

        clean_headers = {k: v for k, v in res_headers.items() if v is not None}
        
        return StreamingResponse(
            stream_generator(), 
            status_code=status_code, 
            media_type=detected_mime, 
            headers=clean_headers
        )
        
    except Exception as e:
        Logger.error("API", f"Stream relay collapsed: {e}")
        raise HTTPException(status_code=500, detail="Relay transmission failure")

@router.get("/stream")
async def get_stream_url(spotify_id: Optional[str] = None, track_name: Optional[str] = None, artist: Optional[str] = None, db: Session = Depends(get_db)):
    """Resolves a streaming link from YouTube with extreme efficiency."""
    loop = asyncio.get_event_loop()
    track = None
    if spotify_id:
        track = db.query(Track).filter(Track.spotify_id == spotify_id).first()
    
    if not track and (track_name and artist):
        # Double filter to ensure we find the exact match in our galaxy
        track = db.query(Track).filter(Track.track_name == track_name, Track.artist == artist).first()
        
    if not track:
        # Create temp entry to anchor the signal
        track = Track(
            spotify_id=spotify_id or f"temp-{int(time.time())}",
            track_name=track_name or "Desconocido",
            artist=artist or "Nebula Signal"
        )
        db.add(track)
        db.commit()
        db.refresh(track)
    
    # --- INSTANT RETURN: Valid cache check ---
    if track.stream_url and track.stream_expiry > time.time() + 300: # 5 min buffer
        import urllib.parse
        quoted_url = urllib.parse.quote(track.stream_url)
        proxied_url = f"http://localhost:8000/api/v1/music/proxy_stream?url={quoted_url}"
        return {
            "url": proxied_url, 
            "stream_url": proxied_url, 
            "meta": {"video_id": track.yt_id, "cached": True}, 
            "popularity": track.popularity
        }
        
    # --- RESOLUTION PATH: Slow but optimized ---
    try:
        # Resolve using executor to prevent event loop stuttering
        stream_info = await loop.run_in_executor(
            None, 
            YTMusicService.search_and_get_stream, 
            track.track_name, 
            track.artist, 
            track.yt_id # Try with existing ID first
        )
        
        if stream_info:
            import math
            views = stream_info.get("view_count", 0)
            track.view_count = views
            track.yt_id = stream_info.get("video_id")
            
            # Popularity calc: log scale (approx 0-100)
            if views > 0:
                track.popularity = min(100, int(math.log10(views) * 10))
            
            track.stream_url = stream_info["stream_url"]
            track.stream_expiry = time.time() + 3600 # 1 hour of orbital stability
            db.commit()
            
            import urllib.parse
            quoted_url = urllib.parse.quote(track.stream_url)
            proxied_url = f"http://localhost:8000/api/v1/music/proxy_stream?url={quoted_url}"
            return {
                "url": proxied_url, 
                "stream_url": proxied_url, 
                "meta": stream_info, 
                "popularity": track.popularity
            }
    except Exception as e:
        db.rollback()
        Logger.error("API", f"Signal resolution crashed: {str(e)}")
        
    # Fallback to existing stream even if slightly expired if we failed to refresh
    if track.stream_url:
        import urllib.parse
        quoted_url = urllib.parse.quote(track.stream_url)
        proxied_url = f"http://localhost:8000/api/v1/music/proxy_stream?url={quoted_url}"
        return {"url": proxied_url, "stream_url": proxied_url, "meta": {"video_id": track.yt_id, "expired": True}}

    raise HTTPException(status_code=404, detail="Frecuencia perdida en el vacío")

@router.get("/favorites")
async def get_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Library fetch for synchronized entities."""
    tracks = db.query(Track).join(Favorite).filter(Favorite.user_id == current_user.id).all()
    return [nebulize_track(t) for t in tracks]

@router.post("/favorites/toggle")
async def toggle_favorite(spotify_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Favorite).filter(Favorite.user_id == current_user.id, Favorite.spotify_id == spotify_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"is_favorite": False}
    else:
        db.add(Favorite(user_id=current_user.id, spotify_id=spotify_id))
        db.commit()
        return {"is_favorite": True}

# --- Background Synchronization ---

def run_deep_sync(user_id: int, token_info: dict):
    from ..db.session import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user: return

        prefs = user.preferences or {}
        prefs["sync_status"] = "in_progress"
        user.preferences = prefs
        db.commit()

        sp = SpotifyService(token_info=token_info)
        
        # 1. Sync Liked Songs
        liked = sp.sync_user_library()
        for t in liked:
            sid = t["id"]
            existing = db.query(Track).filter(Track.spotify_id == sid).first()
            if not existing:
                album = t.get("album", {})
                new_t = Track(
                    spotify_id=sid,
                    track_name=t.get("name", "Unknown"),
                    artist=t.get("artists", [{}])[0].get("name", "Unknown"),
                    album=album.get("name", "Unknown"),
                    thumbnail=album.get("images", [{}])[0].get("url", ""),
                    duration_ms=t.get("duration_ms", 0)
                )
                db.add(new_t)
            
            # Auto-favorite in Nebula if liked in Spotify
            if not db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.spotify_id == sid).first():
                db.add(Favorite(user_id=user_id, spotify_id=sid))
        
        db.commit()
        
        # 2. Sync Recent History
        recent = sp._call_api("current_user_recently_played", limit=50)
        if recent and "items" in recent:
            for item in recent["items"]:
                t = item.get("track")
                if t:
                    sid = t["id"]
                    if not db.query(Track).filter(Track.spotify_id == sid).first():
                        # Minimal add
                        db.add(Track(spotify_id=sid, track_name=t["name"], artist=t["artists"][0]["name"]))
                    db.add(History(user_id=user_id, spotify_id=sid))
        
        db.commit()

        prefs["sync_status"] = "completed"
        user.preferences = prefs
        db.commit()
        Logger.success("SYNC", f"Orbital sync completed for {user.username}")
        
    except Exception as e:
        Logger.error("SYNC", f"Deep sync error: {e}")
        db.rollback()
    finally:
        db.close()

@router.get("/sync")
async def sync_library(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    ULTRA-LIGHT TRIGGER: Delegates the deep orbital synchronization to the worker.
    """
    if not current_user.spotify_token_info:
        raise HTTPException(status_code=400, detail="Spotify connection missing")
        
    import uuid
    job_id = str(uuid.uuid4())
    
    from ..db.models import Job
    new_job = Job(
        id=job_id,
        user_id=current_user.id,
        type="library_sync",
        status="queued",
        message="Preparando sincronización profunda de la biblioteca..."
    )
    db.add(new_job)
    db.commit()

    # Fire Worker
    try:
        import subprocess, sys
        subprocess.Popen([sys.executable, "-m", "app.worker"], start_new_session=True)
    except: pass

    return {"job_id": job_id, "status": "queued"}

@router.get("/sync/status", response_model=SyncStatus)
async def get_sync_status(current_user: User = Depends(get_current_user)):
    status = (current_user.preferences or {}).get("sync_status", "idle")
    return {"status": status, "new_tracks": 0, "total_library": 0, "time_taken": "N/A"}
