from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db.session import get_db
from ..db.models import Track, History, User, Favorite
from ..core.auth_utils import get_current_user
from ..services.spotify_service import SpotifyService
from ..services.ytmusic_service import YTMusicService
import time

from ..services.recommendation_service import RecommendationService
import pandas as pd
import numpy as np

from ..core.logging import Logger
from fastapi.responses import StreamingResponse
import requests
import urllib.parse

router = APIRouter()

@router.get("/tracks")
async def get_tracks(ids: str, db: Session = Depends(get_db)):
    """Fetch track details for multiple IDs from the SQL database."""
    if not ids: return []
    id_list = [id.strip() for id in ids.split(",") if id.strip()]
    
    # Efficient fetch in one SQL query
    found = db.query(Track).filter(Track.spotify_id.in_(id_list)).all()
    
    # Map for easy lookup to maintain original sort order
    track_map = {t.spotify_id: t for t in found}
    return [track_map[sid] for sid in id_list if sid in track_map]

@router.get("/search")
async def search_tracks(q: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Unified search: Focused solely on high-fidelity audio signals."""
    # We focus only on YouTube results now as per latest directive
    results = YTMusicService.search_tracks(q, limit=20)
    return results

@router.post("/played")
async def log_track_play(spotify_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logs a play event in the unified User History table."""
    new_event = History(user_id=current_user.id, spotify_id=spotify_id)
    db.add(new_event)
    db.commit()
    return {"status": "success"}

@router.get("/history")
async def get_user_history(limit: int = 50, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetches personalized history for the logged-in user."""
    results = db.query(Track).join(History).filter(History.user_id == current_user.id).order_by(History.played_at.desc()).limit(limit).all()
    return results

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Calculates biometric stats using SQL repository."""
    total_tracks = db.query(Track).count()
    user_plays = db.query(History).filter(History.user_id == current_user.id).count()
    
    # Calculate average audio features from user history
    # We join History with Track to get features
    history_tracks = db.query(Track).join(History).filter(History.user_id == current_user.id).all()
    
    stats = {
        "total_tracks": total_tracks,
        "total_listened": user_plays,
        "avg_energy": 0,
        "avg_danceability": 0,
        "avg_valence": 0
    }
    
    if history_tracks:
        valid_h = [t for t in history_tracks if t.energy is not None]
        if valid_h:
            stats["avg_energy"] = sum(t.energy for t in valid_h) / len(valid_h)
            stats["avg_danceability"] = sum(t.danceability for t in valid_h) / len(valid_h)
            stats["avg_valence"] = sum(t.valence for t in valid_h) / len(valid_h)
        
    return stats

@router.get("/status")
async def get_status(current_user: User = Depends(get_current_user)):
    """Checks the core system connection levels."""
    sp = SpotifyService(token_info=current_user.spotify_token_info)
    return {
        "connected": sp.is_connected(),
        "user_name": sp.user_name if sp.is_connected() else None,
        "engine": "Nebula Core 2.1",
        "latency": "Calculated by Signal"
    }

@router.get("/recommendations")
async def get_recommendations(limit: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generates cosmic suggestions based on user DNA (History)."""
    # 1. Get user history features
    history_tracks = db.query(Track).join(History).filter(History.user_id == current_user.id).all()
    
    # 2. Get random tracks from general library as candidates
    candidates = db.query(Track).order_by(func.random()).limit(100).all()
    
    valid_h = [t for t in history_tracks if t.energy is not None]
    if not valid_h:
        return candidates[:limit]
        
    avg_energy = sum(t.energy for t in valid_h) / len(valid_h)
    
    scored = []
    for t in candidates:
        e = t.energy if t.energy is not None else 0.5
        score = abs(e - avg_energy)
        scored.append((t, score))
    
    scored.sort(key=lambda x: x[1])
    return [x[0] for x in scored[:limit]]

@router.get("/proxy_stream")
async def proxy_stream(url: str):
    """Pipes an external stream (e.g. YouTube) to local to bypass CORS."""
    try:
        r = requests.get(url, stream=True, timeout=10)
        # Construct response headers based on upstream
        headers = {
            "Content-Type": r.headers.get("Content-Type", "audio/mpeg"),
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache"
        }
        return StreamingResponse(r.iter_content(chunk_size=4096), media_type=headers["Content-Type"], headers=headers)
    except Exception as e:
        Logger.error("API", f"Stream proxy failure: {e}")
        raise HTTPException(status_code=500, detail="Relay collapsed")

@router.get("/stream")
async def get_stream_url(spotify_id: Optional[str] = None, track_name: Optional[str] = None, artist: Optional[str] = None, db: Session = Depends(get_db)):
    """Resolves a streaming link from YouTube, with local relay for CORS stability."""
    # Detect ID prefix
    yt_video_id = None
    if spotify_id and spotify_id.startswith("yt_"):
        yt_video_id = spotify_id.replace("yt_", "")
        
    track = None
    if spotify_id:
        track = db.query(Track).filter(Track.spotify_id == spotify_id).first()
    
    if not track and (track_name and artist):
        track = db.query(Track).filter(Track.track_name == track_name, Track.artist == artist).first()
        
    if not track:
        # Create orbital entry
        track = Track(
            spotify_id=spotify_id or f"temp-{int(time.time())}",
            track_name=track_name or "Desconocido",
            artist=artist or "Nebula Signal",
            yt_id=yt_video_id
        )
        db.add(track)
        db.commit()
    
    # Resolving signal
    if track.stream_url and track.stream_expiry > time.time():
        # Check if URL is still alive (googlevideo links expire fast)
        # But we proxy it anyway below, so we need a fresh URL often
        pass
        
    # Extract fresh signal
    try:
        # Resolve target video ID if not found
        v_id = track.yt_id
        if not v_id:
             v_id = YTMusicService.search_and_get_id(track.track_name, track.artist)
             track.yt_id = v_id
             
        if not v_id: 
            raise ValueError("No video anchor found")
            
        stream_info = YTMusicService.search_and_get_stream(track.track_name, track.artist, video_id=v_id)
        if stream_info:
            track.stream_url = stream_info["stream_url"]
            track.stream_expiry = time.time() + 3600
            db.commit()
            
            # Construct a proxied URL for the frontend
            quoted_url = urllib.parse.quote(track.stream_url)
            proxied_url = f"http://localhost:8000/api/music/proxy_stream?url={quoted_url}"
            return {"url": proxied_url, "stream_url": proxied_url, "meta": stream_info}
    except Exception as e:
        Logger.error("API", f"Signal resolution crashed for {track.track_name}: {str(e)}")
        
    # Fallback to search if everything else fails
    raise HTTPException(status_code=404, detail="Frecuencia perdida")

@router.get("/favorites")
async def get_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Access the user's personal singularity (Favorites)."""
    return db.query(Track).join(Favorite).filter(Favorite.user_id == current_user.id).all()

@router.post("/favorites/toggle")
async def toggle_favorite(spotify_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Toggles track presence in the user's favorites subspace."""
    existing = db.query(Favorite).filter(Favorite.user_id == current_user.id, Favorite.spotify_id == spotify_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"is_favorite": False}
    else:
        db.add(Favorite(user_id=current_user.id, spotify_id=spotify_id))
        db.commit()
        return {"is_favorite": True}

# Synchronization Sub-Process (Non-blocking worker)
def run_deep_sync(user_id: int, token_info: dict):
    from ..db.session import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user: return

        # Mark sync as started in preferences
        prefs = user.preferences or {}
        prefs["sync_status"] = "in_progress"
        prefs["sync_last_start"] = time.time()
        user.preferences = prefs
        db.commit()

        sp = SpotifyService(token_info=token_info)
        
        # Step 0: Helper to ensure track is in database
        def ensure_track(t):
            sid = t["id"]
            existing = db.query(Track).filter(Track.spotify_id == sid).first()
            if not existing:
                artists = t.get("artists", [])
                album = t.get("album", {})
                images = album.get("images", [])
                
                new_t = Track(
                    spotify_id=sid,
                    track_name=t.get("name", "Unknown"),
                    artist=artists[0]["name"] if artists else "Unknown",
                    album=album.get("name", "Unknown"),
                    thumbnail=images[0]["url"] if images else None,
                    duration_ms=t.get("duration_ms", 0)
                )
                db.add(new_t)
                db.flush() # Ensure ID is available
                return new_t
            return existing

        # Phase 1: SYNC LIKED SONGS
        liked_tracks = sp.sync_user_library()
        for i in range(0, len(liked_tracks), 50):
            batch = liked_tracks[i : i + 50]
            batch_ids = [t["id"] for t in batch]
            features_list = sp.get_audio_features(batch_ids)
            features_map = {batch_ids[idx]: f for idx, f in enumerate(features_list) if f}
            
            for t in batch:
                track = ensure_track(t)
                feat = features_map.get(track.spotify_id)
                if feat:
                    track.danceability = feat.get("danceability", track.danceability)
                    track.energy = feat.get("energy", track.energy)
                    track.tempo = feat.get("tempo", track.tempo)
                    track.valence = feat.get("valence", track.valence)
                
                fav = db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.spotify_id == track.spotify_id).first()
                if not fav:
                    db.add(Favorite(user_id=user_id, spotify_id=track.spotify_id))
            db.commit()

        # Phase 2: SYNC RECENTLY PLAYED
        recent_results = sp._call_api("current_user_recently_played", limit=30)
        if recent_results and "items" in recent_results:
            for item in recent_results["items"]:
                t = item.get("track")
                if t:
                    track = ensure_track(t)
                    latest = db.query(History).filter(History.user_id == user_id, History.spotify_id == track.spotify_id).order_by(History.played_at.desc()).first()
                    if not latest or (time.time() - latest.played_at.timestamp() > 900):
                        db.add(History(user_id=user_id, spotify_id=track.spotify_id))
            db.commit()

        # Phase 3: SYNC PLAYLISTS
        from ..db.models import Playlist
        sp_playlists = sp.get_user_playlists(limit=20)
        for pl_meta in sp_playlists:
            pl_id = pl_meta["id"]
            if not db.query(Playlist).filter(Playlist.id == pl_id).first():
                db.add(Playlist(id=pl_id, name=pl_meta["name"], user_id=user_id, is_public=pl_meta["is_public"]))
        
        db.commit()
        
        # Mark as completed
        prefs = user.preferences or {}
        prefs["sync_status"] = "completed"
        prefs["sync_last_end"] = time.time()
        user.preferences = prefs
        db.commit()
        Logger.success("SYNC", f"Orbital sync completed for user {user.username}")
        
    except Exception as e:
        Logger.error("SYNC", f"Background sync failed: {e}")
        db.rollback()
    finally:
        db.close()

@router.get("/sync")
async def sync_library(bt: BackgroundTasks, current_user: User = Depends(get_current_user)):
    """Deep sync of the user's Spotify universe (Non-blocking)."""
    if not current_user.spotify_token_info:
        raise HTTPException(status_code=401, detail="Spotify connection missing")
    
    bt.add_task(run_deep_sync, current_user.id, current_user.spotify_token_info)
    return {"status": "started", "message": "Neural synchronization initialized in secondary layer."}

@router.get("/sync/status")
async def get_sync_status(current_user: User = Depends(get_current_user)):
    status = (current_user.preferences or {}).get("sync_status", "idle")
    return {"status": status}
