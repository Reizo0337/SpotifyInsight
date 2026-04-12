from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json, asyncio, time, uuid, concurrent.futures

from ..db.session import get_db, SessionLocal
from ..db.models import Playlist, PlaylistTrack, Track, User
from ..core.auth_utils import get_current_user
from ..services.spotify_service import SpotifyService
from ..services.ytmusic_service import YTMusicService
from ..services.playlist_scraper import scrape_playlist_tracks
from ..core.logging import Logger
from ..schemas import PlaylistBase, PlaylistCreate, PlaylistImport, TrackBase

router = APIRouter()

@router.get("/")
async def get_playlists(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetches all playlists owned by the authenticated user, including track IDs."""
    playlists = db.query(Playlist).filter(Playlist.user_id == current_user.id).all()
    result = []
    for pl in playlists:
        track_ids = [pt.spotify_id for pt in pl.tracks]
        
        # Determine thumbnail signal from the first track in the sequence
        thumbnail = None
        if pl.tracks:
            first_track_link = pl.tracks[0]
            first_track = db.query(Track).filter(Track.spotify_id == first_track_link.spotify_id).first()
            if first_track:
                thumbnail = first_track.thumbnail

        result.append({
            "id": pl.id,
            "name": pl.name,
            "is_public": pl.is_public,
            "tracks": track_ids,
            "thumbnail": thumbnail
        })
    return result

@router.post("/")
async def create_playlist(req: PlaylistCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Creates a new empty playlist tied to the user."""
    new_pl = Playlist(
        id=str(uuid.uuid4()), 
        name=req.name, 
        user_id=current_user.id, 
        is_public=req.is_public
    )
    db.add(new_pl)
    db.commit()
    db.refresh(new_pl)
    return {"id": new_pl.id, "name": new_pl.name, "is_public": new_pl.is_public, "tracks": []}

@router.delete("/{playlist_id}")
async def delete_playlist(playlist_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Removes a playlist and its track associations for the owner."""
    pl = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not pl: raise HTTPException(status_code=404, detail="No encontramos esa lista")
    
    db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).delete()
    db.delete(pl)
    db.commit()
    return {"status": "success"}

@router.post("/{playlist_id}/tracks")
async def add_track_to_playlist(playlist_id: str, spotify_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Associates a track with a playlist in SQL."""
    pl = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not pl: raise HTTPException(status_code=404, detail="No tienes acceso a esta lista")
    
    exists = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id, PlaylistTrack.spotify_id == spotify_id).first()
    if exists: return {"status": "already_exists"}
    
    new_pt = PlaylistTrack(playlist_id=playlist_id, spotify_id=spotify_id)
    db.add(new_pt)
    db.commit()
    return {"status": "success"}

@router.get("/{playlist_id}/tracks")
async def get_playlist_tracks(playlist_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetches all tracks associated with a specific playlist, with proxied audio signals."""
    # Check ownership or visibility
    pl = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not pl: raise HTTPException(status_code=404, detail="Lista no encontrada")
    if not pl.is_public and pl.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
        
    tracks = db.query(Track).join(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).all()
    
    results = []
    for t in tracks:
        stream = None
        if t.stream_url and (t.stream_expiry and t.stream_expiry > time.time() + 120):
            import urllib.parse
            stream = f"/api/v1/music/proxy_stream?url={urllib.parse.quote(t.stream_url)}"
            
        results.append({
            "spotify_id": t.spotify_id,
            "track_name": t.track_name,
            "artist": t.artist or "Unknown",
            "album": t.album or "Unknown",
            "thumbnail": t.thumbnail or "",
            "duration_ms": t.duration_ms or 0,
            "yt_id": t.yt_id,
            "stream_url": stream,
        })
    return results

@router.get("/spotify-info")
async def get_spotify_playlist_info(url: str, current_user: User = Depends(get_current_user)):
    """Fetches metadata for a Spotify playlist by URL."""
    sp = SpotifyService(token_info=current_user.spotify_token_info)
    pid = url.split("/")[-1].split("?")[0].split(":")[-1]
    info = sp.get_playlist_metadata(pid)
    if not info:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Fallback: if API says 0 but it's a valid response, try scraper for count
    if info.get("track_count") == 0:
        Logger.info("API", f"Spotify API returned 0 tracks for {pid}, trying scraper fallback...")
        scraped = await asyncio.get_event_loop().run_in_executor(None, scrape_playlist_tracks, pid)
        if scraped:
            info["track_count"] = len(scraped)
            info["total"] = len(scraped)
            Logger.info("API", f"Scraper found {len(scraped)} tracks as fallback.")
            
    return info

@router.post("/import/start")
async def start_playlist_import(
    req: PlaylistImport, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    ULTRA-LIGHT TRIGGER: Handled by architectural mandate.
    Validates, enqueues, and delegates to the worker.
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    # 1. Clean URL/ID
    pid = req.url.split("playlist/")[-1].split("?")[0] if "playlist/" in req.url else req.url
    
    # 2. Persist Job record
    from ..db.models import Job
    new_job = Job(
        id=job_id,
        user_id=current_user.id,
        type="playlist_import",
        status="queued",
        message="Esperando turno en el Escuadrón de Sanación...",
        result={"playlist_id": pid, "name": req.name, "target_playlist_id": req.target_playlist_id}
    )
    db.add(new_job)
    db.commit()

    # 3. Fire-and-forget sub-process (as per mandate for isolation)
    try:
        import subprocess, sys
        subprocess.Popen([sys.executable, "-m", "app.worker"], start_new_session=True)
    except: pass

    return {"job_id": job_id, "status": "queued"}

@router.get("/import/status/{job_id}")
async def get_import_status(
    job_id: str, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """LIGHTWEIGHT POLLING: Returns the current state of the background job."""
    from ..db.models import Job
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "result": job.result,
        "error": job.error
    }
