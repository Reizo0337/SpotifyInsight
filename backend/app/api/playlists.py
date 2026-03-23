from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json, asyncio, time, uuid

from ..db.session import get_db
from ..db.models import Playlist, PlaylistTrack, Track, User
from ..core.auth_utils import get_current_user
from ..services.spotify_service import SpotifyService
from ..services.ytmusic_service import YTMusicService
from ..services.playlist_scraper import scrape_playlist_tracks
from ..core.logging import Logger

router = APIRouter()

@router.get("/")
async def get_playlists(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetches all playlists owned by the authenticated user."""
    return db.query(Playlist).filter(Playlist.user_id == current_user.id).all()

@router.post("/")
async def create_playlist(name: str, is_public: bool = True, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Creates a new empty playlist tied to the user."""
    new_pl = Playlist(id=str(uuid.uuid4()), name=name, user_id=current_user.id, is_public=is_public)
    db.add(new_pl)
    db.commit()
    db.refresh(new_pl)
    return new_pl

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
    # Check ownership
    pl = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == current_user.id).first()
    if not pl: raise HTTPException(status_code=404, detail="No tienes acceso a esta lista")
    
    # Check if already in playlist
    exists = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id, PlaylistTrack.spotify_id == spotify_id).first()
    if exists: return {"status": "already_exists"}
    
    new_pt = PlaylistTrack(playlist_id=playlist_id, spotify_id=spotify_id)
    db.add(new_pt)
    db.commit()
    return {"status": "success"}

# --- SSE Stream Logic for Spotify Imports (Integrated with SQL) ---

@router.get("/import/stream")
async def import_spotify_stream(playlist_id: str, name: str, target_playlist_id: str = "", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Parallel SSE streaming import using MySQL as the primary store.
    Sends real-time JSON updates.
    """
    sp = SpotifyService()
    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=6)

    async def event_generator():
        def send(type: str, **kwargs):
            return f"data: {json.dumps({'type': type, **kwargs})}\n\n"

        loop = asyncio.get_event_loop()

        # Step 1: Destination playlist shell
        if target_playlist_id:
            final_pl_id = target_playlist_id
        else:
            new_pl = Playlist(id=str(uuid.uuid4()), name=name, user_id=current_user.id)
            db.add(new_pl)
            db.commit()
            db.refresh(new_pl)
            final_pl_id = new_pl.id
        yield send("playlist_created", id=final_pl_id, name=name)

        # Step 2: Extract tracks via scraping
        yield send("status", message="Escaneando el universo Spotify...")
        scraped = await loop.run_in_executor(None, scrape_playlist_tracks, playlist_id)
        if not scraped:
            yield send("error", message="La nebulosa está vacía o es privada.")
            return

        total = len(scraped)
        yield send("total", count=total)

        # Step 3: Fast Batch Enrichment
        track_map = {t["spotify_id"]: t for t in scraped if t.get("spotify_id")}
        all_ids = list(track_map.keys())
        
        if sp.is_connected():
            for i in range(0, len(all_ids), 50):
                batch = all_ids[i:i+50]
                try:
                    res = await loop.run_in_executor(None, lambda b=batch: sp._call_api("tracks", b))
                    if res and "tracks" in res:
                        for f in res["tracks"]:
                            if not f: continue
                            tid = f["id"]
                            if tid in track_map:
                                artists = f.get("artists", [])
                                album = f.get("album", {})
                                track_map[tid].update({
                                    "artist": artists[0]["name"] if artists else "Unknown",
                                    "album": album.get("name", "Unknown"),
                                    "thumbnail": album.get("images", [{}])[0].get("url", ""),
                                    "duration_ms": f.get("duration_ms", 0),
                                    "popularity": f.get("popularity", 0),
                                })
                except Exception as e:
                    Logger.warning("IMPORT", f"Batch Spotify error: {e}")
                await asyncio.sleep(0)

        # Save to MySQL Tracks repository and associate with Playlist
        for tid, t in track_map.items():
            # Merge track into database (upsert)
            existing_t = db.query(Track).filter(Track.spotify_id == tid).first()
            if not existing_t:
                new_t = Track(
                    spotify_id=tid, 
                    track_name=t.get("track_name", "Unknown"),
                    artist=t.get("artist", "Unknown"),
                    album=t.get("album", "Unknown"),
                    thumbnail=t.get("thumbnail", ""),
                    duration_ms=t.get("duration_ms", 0),
                    popularity=t.get("popularity", 0)
                )
                db.add(new_t)
            
            # Link to Playlist
            exists_link = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == final_pl_id, PlaylistTrack.spotify_id == tid).first()
            if not exists_link:
                db.add(PlaylistTrack(playlist_id=final_pl_id, spotify_id=tid))
        
        db.commit()
        yield send("phase2_start", message="Canciones añadidas. Sincronizando audio en paralelo...")

        # Step 4: Parallel YouTube Linking (6 threads)
        needs_yt = []
        # Pre-check which tracks in DB still need a YT ID
        # ... logic skipped for brevity but would query Tracks table for NULL yt_id
        # For simplicity in this chunk, iterate scraped
        for tid, t in track_map.items():
            needs_yt.append((tid, t.get("track_name", "Unknown"), t.get("artist", "Unknown")))

        sem = asyncio.Semaphore(6)
        async def fetch_yt(tid, tn, ar):
            async with sem:
                try:
                    yt_result = await loop.run_in_executor(executor, lambda: YTMusicService.search_and_get_stream(tn, ar))
                    if yt_result:
                        db.query(Track).filter(Track.spotify_id == tid).update({
                            "yt_id": yt_result.get("video_id", ""),
                            "stream_url": yt_result.get("stream_url", ""),
                            "stream_expiry": time.time() + 18000,
                            "duration_ms": int(yt_result.get("duration", 0)) * 1000
                        })
                        db.commit()
                except: pass

        tasks = [asyncio.create_task(fetch_yt(tid, tn, ar)) for tid, tn, ar in needs_yt]
        reported = 0
        while reported < len(tasks):
            done = sum(1 for t in tasks if t.done())
            if done > reported:
                reported = done
                yield send("progress", current=reported, total=len(tasks), phase="yt", phase_label=f"Audio: {reported}/{len(tasks)}")
            await asyncio.sleep(0.5)

        executor.shutdown(wait=False)
        yield send("done", id=final_pl_id, total=total)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
