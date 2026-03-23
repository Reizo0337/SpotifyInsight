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
from pydantic import BaseModel

from ..services.spotify_service import SpotifyService
from ..services.data_service import DataService
from ..services.recommendation_service import RecommendationService
from ..services.audio_analysis_service import AudioAnalysisService
from ..services.ytmusic_service import YTMusicService
from ..models.schemas import TrackBase, TrackFeatures, SyncStatus
import json
from ..core.logging import Logger
from ..services.playlist_scraper import scrape_playlist_tracks

router = APIRouter()

class CreatePlaylistRequest(BaseModel):
    name: str
    is_public: bool = True

class ImportPlaylistRequest(BaseModel):
    playlist_id: str
    name: str
    target_playlist_id: Optional[str] = None

@router.get("/status")
async def get_status():
    """Checks Spotify connection status."""
    sp = SpotifyService()
    return {"connected": sp.is_connected(), "user": sp.user_name}

@router.get("/user-profile")
async def get_user_profile():
    sp = SpotifyService()
    user = sp.get_user_profile()
    if not user:
        raise HTTPException(status_code=401, detail="Spotify not connected")
    return user

@router.get("/sync-library")
async def sync_library():
    sp = SpotifyService()
    if not sp.is_connected():
        raise HTTPException(status_code=401, detail="Spotify not connected")
    
    start_time = time.time()
    try:
        new_tracks = sp.sync_user_library()
        lib_df = DataService.load_library()
        elapsed = time.time() - start_time
        
        status = SyncStatus(
            status="success",
            new_tracks=new_tracks,
            total_library=len(lib_df),
            time_taken=f"{elapsed:.2f}s"
        )
        return status
    except Exception as e:
        Logger.error("API", f"Sync failed: {str(e)}")
        return SyncStatus(
            status="error",
            new_tracks=0,
            total_library=0,
            time_taken="0s"
        )

@router.get("/recommendations")
async def get_recommendations(limit: int = 20, song: Optional[str] = None):
    sp = SpotifyService()
    lib_df = DataService.load_library()
    user_df = DataService.load_user_data(sp.user_id)
    
    spotify_recs = []
    
    # 1. Try to get seeds from recent history for Spotify engine
    if sp.is_connected() and not user_df.empty:
        recent_ids = user_df.sort_values("played_at", ascending=False)["spotify_id"].unique()[:5].tolist()
        if recent_ids:
            spotify_recs = sp.get_recommendations_from_spotify(seed_tracks=recent_ids, limit=limit * 2)

    # 2. Vibe mode (Local-led content matching) or discovery
    target_profile = None
    if song:
        target_track = await _prepare_target_track(song, sp, lib_df)
        if target_track and "target_features" in target_track and target_track["target_features"]:
            # Ensure target_features is a dict with correct keys
            target_profile = pd.DataFrame([target_track["target_features"]])
    elif not user_df.empty and not lib_df.empty:
        # Join user_df with lib_df to get features
        profile_tracks = user_df.merge(lib_df, on="spotify_id", how="inner")
        if not profile_tracks.empty:
            target_profile = profile_tracks

    if lib_df.empty: 
        if spotify_recs: return spotify_recs[:limit]
        raise HTTPException(status_code=404, detail="Library empty.")
        
    return RecommendationService.get_recommendations(
        lib_df, 
        user_profile_tracks=target_profile if target_profile is not None else pd.DataFrame(columns=lib_df.columns), 
        n_recommendations=limit,
        spotify_candidates=spotify_recs
    )

async def _prepare_target_track(query: str, sp: SpotifyService, lib_df: pd.DataFrame):
    """Finds and enriches a track for seeds."""
    track = sp.search_track(query)
    if not track: return None
    
    # Check if already in library
    if not lib_df.empty:
        mask = lib_df["spotify_id"] == track["id"]
        if mask.any():
            track["target_features"] = lib_df[mask].iloc[0].to_dict()
    
    # If not in library, try to get from Spotify
    if "target_features" not in track and sp.is_connected():
        features = sp.get_track_features(track["id"])
        track["target_features"] = features
        
    return track

@router.get("/search")
async def search(q: str):
    sp = SpotifyService()
    lib_df = DataService.load_library()
    local_results = []
    if not lib_df.empty:
        mask = (lib_df['track_name'].str.contains(q, case=False, na=False)) | \
               (lib_df['artist'].str.contains(q, case=False, na=False))
        local_results = lib_df[mask].head(10).replace({np.nan: None}).to_dict('records')

    spotify_results = []
    if sp.is_connected():
        spotify_results = sp.search_tracks(q, limit=10)
    
    return {
        "local": local_results,
        "spotify": spotify_results
    }

# FIXED: Standardized stream endpoint for frontend
@router.get("/stream")
async def stream_track_legacy(spotify_id: Optional[str] = None, track: Optional[str] = None, artist: Optional[str] = None):
    if not spotify_id and (not track or not artist):
        raise HTTPException(status_code=400, detail="Missing identifier")
    
    lib_df = DataService.load_library()
    mask = pd.Series(False, index=lib_df.index)
    
    if spotify_id:
        mask = lib_df["spotify_id"] == spotify_id
    
    # If not found by ID, try fuzzy name/artist if provided
    if not mask.any() and track and artist:
        mask = (lib_df["track_name"].str.lower() == track.lower()) & (lib_df["artist"].str.lower() == artist.lower())

    yt_id = None
    stream_url = None
    
    if not mask.any():
        # New track or not found
        if spotify_id:
            sp = SpotifyService()
            track_info = sp._call_api("track", spotify_id)
            if track_info:
                DataService.update_track_metadata(spotify_id, {}, track_info["name"], track_info["artists"][0]["name"])
                lib_df = DataService.load_library()
                mask = lib_df["spotify_id"] == spotify_id
        else:
            # We must search it
            yt_id = YTMusicService.search_and_get_id(track, artist)

    if mask.any():
        row = lib_df[mask].iloc[0]
        yt_id = row.get("yt_id")
        stream_url = row.get("stream_url")
        expiry = row.get("stream_expiry", 0)
        if time.time() > expiry: stream_url = None
        spotify_id = row["spotify_id"]

    if not yt_id and (track and artist):
        yt_id = YTMusicService.search_and_get_id(track, artist)
        if yt_id and mask.any():
            lib_df.loc[mask, "yt_id"] = yt_id
            DataService.save_library(lib_df)

    if not stream_url and yt_id:
        stream_url, expiry = YTMusicService.get_streaming_url(yt_id)
        if stream_url and mask.any():
            lib_df.loc[mask, "stream_url"] = stream_url
            lib_df.loc[mask, "stream_expiry"] = expiry
            DataService.save_library(lib_df)

    if stream_url: return {"url": stream_url}
    raise HTTPException(status_code=404, detail="Stream not found")

@router.get("/explore/recent")
async def get_recent_listened():
    sp = SpotifyService()
    user_df = DataService.load_user_data(sp.user_id)
    local_recent = []
    if not user_df.empty:
        local_recent = user_df.sort_values("played_at", ascending=False).head(10).replace({np.nan: None}).to_dict("records")
    
    spotify_recent = []
    if sp.is_connected():
        spotify_recent = sp.get_recently_played(limit=10)
        
    return {"local": local_recent, "spotify": spotify_recent}

# FIXED: Aliased for frontend compatibility
@router.post("/music/played")
@router.post("/track/played")
async def track_played(track: TrackBase):
    sp = SpotifyService()
    DataService.add_to_history(sp.user_id, track.model_dump())
    return {"status": "success"}

# FIXED: history endpoint for frontend
@router.get("/history")
@router.get("/search/recently-played")
async def get_history(limit: int = 25):
    sp = SpotifyService()
    user_df = DataService.load_user_data(sp.user_id)
    if user_df.empty: return []
    recent = user_df.sort_values("played_at", ascending=False).head(limit).replace({np.nan: None})
    return recent.to_dict("records")

@router.get("/stats")
async def get_stats():
    """Simple stats for dashboard."""
    lib_df = DataService.load_library()
    sp = SpotifyService()
    user_df = DataService.load_user_data(sp.user_id)
    return {
        "total_tracks": len(lib_df),
        "total_listened": len(user_df),
        "spotify_connected": sp.is_connected()
    }

@router.get("/tracks")
async def get_tracks_by_ids(ids: str):
    """Returns metadata for a list of spotify_ids."""
    if not ids: return []
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    
    lib_df = DataService.load_library()
    if lib_df.empty: return []
    
    # Filter and maintain order
    lib_df = lib_df.set_index("spotify_id")
    # We use reindex to both filter and SORT according to the requested id_list
    # Any IDs not found in index will result in NaN rows, which we drop
    found_tracks = lib_df.reindex(id_list).dropna(how="all").reset_index()
    
    # CRITICAL: Replace NaN values with None/empty string for JSON compliance
    # Standard json.dumps cannot handle NaNs (common in pandas/numpy)
    found_tracks = found_tracks.replace({np.nan: None})
    
    # Convert back to list of dicts
    return found_tracks.to_dict("records")

@router.get("/playlists")
async def get_playlists():
    return DataService.load_playlists()

@router.post("/playlists")
async def create_playlist(req: CreatePlaylistRequest):
    pl = DataService.create_playlist(req.name, is_public=req.is_public)
    if not pl: raise HTTPException(status_code=500, detail="Failed")
    return pl

@router.post("/playlists/{playlist_id}/tracks")
async def add_track_to_playlist_endpoint(playlist_id: str, track: TrackBase):
    if DataService.add_track_to_playlist(playlist_id, track.model_dump()):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Not found")

@router.get("/spotify/playlist-info")
async def get_spotify_playlist_info(url: str):
    sp = SpotifyService()
    if not sp.is_connected():
        raise HTTPException(status_code=401, detail="Spotify not connected")
    
    pid = url.split("/")[-1].split("?")[0].split(":")[-1]
    info = sp.get_playlist_metadata(pid)
    if not info:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return info

@router.post("/spotify/playlists/import")
async def import_spotify_playlist(req: ImportPlaylistRequest):
    """Simple (non-streaming) import - kept for compatibility."""
    sp = SpotifyService()
    if not sp.is_connected():
        raise HTTPException(status_code=401, detail="Spotify not connected")
    
    if req.target_playlist_id:
        final_pl_id = req.target_playlist_id
    else:
        new_pl = DataService.create_playlist(req.name)
        if not new_pl: raise HTTPException(status_code=500, detail="Failed creating playlist")
        final_pl_id = new_pl["id"]

    tracks = sp.get_playlist_tracks(req.playlist_id)
    if not tracks:
        return {"status": "ok", "id": final_pl_id, "track_count": 0, "warning": "Playlist was empty or inaccessible"}
    
    count = 0
    for t in tracks:
        t_id = t.get("spotify_id")
        if not t_id: continue
        DataService.update_track_metadata(t_id, t, t.get("track_name", "Unknown"), t.get("artist", "Unknown"))
        if DataService.add_track_to_playlist(final_pl_id, {"spotify_id": t_id}):
            count += 1
            
    return {"status": "ok", "id": final_pl_id, "track_count": count}


@router.get("/spotify/playlists/import/stream")
async def import_spotify_playlist_stream(playlist_id: str, name: str, target_playlist_id: str = ""):
    """
    SSE streaming import: scrape → enrich → get YT links → save.
    Sends JSON progress events to the client.
    """
    sp = SpotifyService()

    # Use a thread pool with more workers for concurrent yt-dlp calls
    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=6)

    async def event_generator():
        def send(msg_type: str, **kwargs):
            data = json.dumps({"type": msg_type, **kwargs})
            return f"data: {data}\n\n"

        loop = asyncio.get_event_loop()

        # Step 1: Create playlist shell
        if target_playlist_id:
            final_pl_id = target_playlist_id
        else:
            new_pl = DataService.create_playlist(name)
            if not new_pl:
                yield send("error", message="No se pudo crear la playlist")
                return
            final_pl_id = new_pl["id"]
        yield send("playlist_created", id=final_pl_id, name=name)

        # Step 2: Scrape the track list
        yield send("status", message="Obteniendo lista de canciones...")
        await asyncio.sleep(0)
        scraped = await loop.run_in_executor(None, scrape_playlist_tracks, playlist_id)
        if not scraped:
            yield send("error", message="No se encontraron canciones. ¿Es pública la playlist?")
            return

        total = len(scraped)
        yield send("total", count=total)

        # Step 3: BATCH enrich Spotify metadata (50 tracks at a time — fast!)
        yield send("status", message=f"Obteniendo metadatos de {total} canciones...")
        track_map = {t["spotify_id"]: t for t in scraped if t.get("spotify_id")}
        all_ids = list(track_map.keys())

        if sp.is_connected():
            for i in range(0, len(all_ids), 50):
                batch = all_ids[i:i+50]
                try:
                    res = await loop.run_in_executor(None, lambda b=batch: sp._call_api("tracks", b))
                    if res and "tracks" in res:
                        for full in res["tracks"]:
                            if not full: continue
                            tid = full.get("id")
                            if tid and tid in track_map:
                                artists = full.get("artists", [])
                                album = full.get("album", {})
                                images = album.get("images", [])
                                track_map[tid].update({
                                    "artist": artists[0]["name"] if artists else track_map[tid]["artist"],
                                    "album": album.get("name", "Unknown"),
                                    "thumbnail": images[0]["url"] if images else None,
                                    "duration_ms": full.get("duration_ms", 0),
                                    "popularity": full.get("popularity", 0),
                                })
                except Exception as e:
                    Logger.warning("IMPORT", f"Batch Spotify enrichment failed: {e}")
                await asyncio.sleep(0)

        # Save all metadata to library and add to playlist (Phase 1 complete)
        lib = DataService.load_library()
        for tid, t in track_map.items():
            DataService.update_track_metadata(tid, t, t.get("track_name", "Unknown"), t.get("artist", "Unknown"))
            DataService.add_track_to_playlist(final_pl_id, {"spotify_id": tid})

        yield send("phase2_start", message="Canciones añadidas. Obteniendo links de YouTube en paralelo...")

        # Step 4: PARALLEL YT analysis — 6 concurrent workers
        # Check which tracks already have a YT id cached
        lib = DataService.load_library()
        needs_yt = []
        for tid, t in track_map.items():
            already = False
            if not lib.empty and tid in lib["spotify_id"].values:
                row = lib[lib["spotify_id"] == tid].iloc[0]
                yt_val = str(row["yt_id"]) if "yt_id" in row.index else ""
                already = yt_val not in ("", "nan", "None", "0")
            if not already:
                needs_yt.append((tid, t.get("track_name", "Unknown"), t.get("artist", "Unknown")))

        yt_total = len(needs_yt)
        yt_done = 0
        sem = asyncio.Semaphore(6)  # max 6 concurrent yt-dlp searches

        async def fetch_yt(tid, track_name, artist):
            nonlocal yt_done
            async with sem:
                try:
                    yt_result = await loop.run_in_executor(
                        executor,
                        lambda tn=track_name, ar=artist: YTMusicService.search_and_get_stream(tn, ar)
                    )
                    if yt_result:
                        DataService.update_track_metadata(tid, {
                            "yt_id": yt_result.get("video_id", ""),
                            "stream_url": yt_result.get("stream_url", ""),
                            "stream_expiry": time.time() + 3600 * 5,
                            "duration_ms": int(yt_result.get("duration", 0)) * 1000,
                        }, track_name, artist)
                except Exception as e:
                    Logger.warning("IMPORT", f"YT fetch failed for {track_name}: {e}")
                finally:
                    yt_done += 1

        # Create all tasks and run them concurrently, reporting progress as they complete
        tasks = [asyncio.create_task(fetch_yt(tid, tn, ar)) for tid, tn, ar in needs_yt]

        reported = 0
        while reported < len(tasks):
            done_count = sum(1 for t in tasks if t.done())
            if done_count > reported:
                reported = done_count
                yield send("progress", current=reported, total=yt_total,
                           track="", artist="",
                           phase="yt", phase_label=f"YouTube: {reported}/{yt_total}")
            if reported < len(tasks):
                await asyncio.sleep(0.5)

        await asyncio.gather(*tasks, return_exceptions=True)
        executor.shutdown(wait=False)

        yield send("done", id=final_pl_id, track_count=total)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

@router.delete("/playlists/{playlist_id}/tracks/{spotify_id}")
async def remove_track_from_playlist(playlist_id: str, spotify_id: str):
    playlists = DataService.load_playlists()
    for pl in playlists:
        if pl["id"] == playlist_id:
            if spotify_id in pl["tracks"]:
                pl["tracks"].remove(spotify_id)
                DataService.save_playlists(playlists)
            return {"status": "success", "playlist": pl}
    raise HTTPException(status_code=404, detail="Not found")

@router.get("/favorites")
async def get_favorites():
    return DataService.load_favorites()

@router.post("/favorites/toggle")
async def toggle_favorite(track: TrackBase):
    is_favorite = DataService.toggle_favorite(track.model_dump())
    return {"status": "success", "is_favorite": is_favorite}
