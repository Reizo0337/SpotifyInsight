import asyncio
import time
from sqlalchemy.orm import Session
from ..db.session import SessionLocal
from ..db.models import Track
from .spotify_service import SpotifyService
from .ytmusic_service import YTMusicService
from .audio_analysis_service import AudioAnalysisService
from ..core.logging import Logger

class EnrichmentService:
    @staticmethod
    async def enrich_incomplete_tracks():
        """
        Background worker that finds tracks with 0 duration or missing data
        and fixes them using Spotify/YT APIs.
        """
        while True:
            db = SessionLocal()
            try:
                # Find tracks that are missing core metadata OR audio DNA analysis
                incomplete = db.query(Track).filter(
                    (Track.duration_ms == 0) | 
                    (Track.yt_id == None) | 
                    (Track.thumbnail == None) | 
                    (Track.thumbnail == "") |
                    (Track.energy == 0) |
                    (Track.danceability == 0)
                ).limit(10).all()
                
                if not incomplete:
                    await asyncio.sleep(60) # All signals clear, sleep
                    continue
                
                sp = SpotifyService()
                for track in incomplete:
                    reasons = []
                    if track.duration_ms == 0: reasons.append("Missing Duration")
                    if not track.yt_id: reasons.append("Missing YT Anchor")
                    if not track.thumbnail or track.thumbnail == "nebula-default": reasons.append("Missing Visual Signal")
                    if track.energy == 0: reasons.append("Missing Energy DNA")
                    if track.danceability == 0: reasons.append("Missing Rhythmical DNA")
                    
                    Logger.info("ENRICH", f"Healing {track.track_name} | Diagnosis: {', '.join(reasons)}")
                    
                    fixed_anything = False
                    
                    # Ensure YT ID is at least extracted from spotify_id if it's a YT source
                    if not track.yt_id:
                        if track.spotify_id.startswith("yt_"):
                            track.yt_id = track.spotify_id.replace("yt_", "")
                            fixed_anything = True
                        else:
                            v_id = YTMusicService.search_and_get_id(track.track_name, track.artist)
                            if v_id: 
                                track.yt_id = v_id
                                fixed_anything = True
                            else: 
                                track.yt_id = "NULL_ANCHOR"
                                fixed_anything = True

                    # 1. METADATA (Thumbnail, Album, Popularity)
                    if not track.thumbnail or track.thumbnail == "nebula-default" or track.duration_ms == 0:
                        # Try Spotify first
                        if not track.spotify_id.startswith("yt_"):
                            try:
                                sp_data = sp._call_api("track", track.spotify_id)
                                if sp_data:
                                    track.duration_ms = sp_data.get("duration_ms", track.duration_ms)
                                    track.popularity = sp_data.get("popularity", track.popularity)
                                    track.album = sp_data.get("album", {}).get("name", track.album)
                                    imgs = sp_data.get("album", {}).get("images", [])
                                    if imgs: track.thumbnail = imgs[0]["url"]
                                    fixed_anything = True
                            except: pass

                        # Fallback to iTunes for Metadata
                        if not track.thumbnail or track.thumbnail == "nebula-default" or track.popularity == 0:
                            itunes = AudioAnalysisService.get_itunes_metadata(track.track_name, track.artist)
                            if itunes and itunes["thumbnail"]:
                                track.thumbnail = itunes["thumbnail"]
                                track.popularity = itunes["popularity"]
                                track.album = itunes.get("album", track.album)
                                fixed_anything = True
                                
                        # Final resort for visual: YT Music direct
                        if not track.thumbnail or track.thumbnail == "nebula-default":
                            yt_info = YTMusicService.search_and_get_stream(track.track_name, track.artist, video_id=track.yt_id if track.yt_id != "NULL_ANCHOR" else None)
                            if yt_info and yt_info.get("thumbnail"):
                                track.thumbnail = yt_info["thumbnail"]
                                track.duration_ms = yt_info["duration"] * 1000 if track.duration_ms == 0 else track.duration_ms
                                fixed_anything = True

                    # 2. AUDIO DNA ANALYSIS (Energy, Danceability, etc.)
                    if track.energy == 0 or track.danceability == 0:
                        preview_url = AudioAnalysisService.get_preview_from_itunes(track.track_name, track.artist)
                        if preview_url:
                            dna = AudioAnalysisService.analyze_preview(preview_url)
                            if dna:
                                track.energy = dna["energy"]
                                track.danceability = dna["danceability"]
                                track.tempo = dna["tempo"]
                                track.valence = dna["valence"]
                                fixed_anything = True
                    
                    # Mandatory resolution state to break loop
                    if not track.thumbnail: track.thumbnail = "nebula-placeholder"
                    if track.energy == 0: track.energy = 0.001
                    if track.danceability == 0: track.danceability = 0.001
                    if track.duration_ms == 0: track.duration_ms = 180000 
                    
                    db.commit()
                    Logger.success("ENRICH", f"Signal stabilized: {track.track_name}")
                    await asyncio.sleep(1.5) # Asynchronous throttle
                
            except Exception as e:
                Logger.error("ENRICH", f"Worker crashed: {e}")
                # traceback.print_exc()
            finally:
                db.close()
            
            await asyncio.sleep(5)

def start_enrichment_worker():
    loop = asyncio.get_event_loop()
    loop.create_task(EnrichmentService.enrich_incomplete_tracks())
