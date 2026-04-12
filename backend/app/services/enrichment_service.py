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
    def heal_small_batch():
        """
        Processes a single small batch of incomplete tracks.
        Returns True if something was healed, False otherwise.
        """
        db = SessionLocal()
        try:
            # Find tracks missing core metadata OR audio DNA analysis
            # We only pick a few to keep the worker responsive
            incomplete = db.query(Track).filter(
                (Track.duration_ms == 0) | 
                (Track.yt_id == None) | 
                (Track.thumbnail == None) | 
                (Track.thumbnail == "") |
                (Track.thumbnail == "nebula-default") |
                (Track.thumbnail == "nebula-placeholder") |
                (Track.energy == 0) |
                (Track.danceability == 0) |
                (Track.view_count == 0)
            ).limit(5).all()
            
            if not incomplete:
                return False
            
            sp = SpotifyService()
            for track in incomplete:
                fixed_anything = False
                
                # 1. YT ANCHOR + VIEW COUNT (Essential for playback & Fame Chart)
                if not track.yt_id or track.yt_id == "NULL_ANCHOR" or track.view_count == 0:
                    if track.spotify_id and track.spotify_id.startswith("yt_"):
                        track.yt_id = track.spotify_id.replace("yt_", "")
                        fixed_anything = True
                    elif not track.yt_id or track.yt_id == "NULL_ANCHOR":
                        v_id = YTMusicService.search_and_get_id(track.track_name, track.artist)
                        if v_id: 
                            track.yt_id = v_id
                        else: 
                            track.yt_id = "NULL_ANCHOR"
                        fixed_anything = True
                    
                    # Fetch view count + thumbnail via yt-dlp if we have a valid YT ID
                    if track.yt_id and track.yt_id != "NULL_ANCHOR" and (track.view_count == 0 or not track.thumbnail or "nebula" in track.thumbnail):
                        # Always set a better fallback than nebula-placeholder if we have a YT ID
                        if track.yt_id and (not track.thumbnail or "nebula" in track.thumbnail):
                             track.thumbnail = f"https://i.ytimg.com/vi/{track.yt_id}/hqdefault.jpg"
                             fixed_anything = True

                        try:
                            import yt_dlp
                            ydl_opts = {
                                "quiet": True, 
                                "no_warnings": True, 
                                "extract_flat": False, 
                                "skip_download": True,
                                "cookiesfrombrowser": ("brave",)
                            }
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                info = ydl.extract_info(f"https://www.youtube.com/watch?v={track.yt_id}", download=False)
                                if info:
                                    if track.view_count == 0:
                                        track.view_count = info.get("view_count", 0) or 0
                                    # Overwrite pattern with real thumb if possible
                                    track.thumbnail = info.get("thumbnail", track.thumbnail)
                                    if not track.release_date and info.get("upload_date"):
                                        # Convert YYYYMMDD to YYYY-MM-DD
                                        ud = info.get("upload_date")
                                        if len(ud) == 8:
                                            track.release_date = f"{ud[:4]}-{ud[4:6]}-{ud[6:]}"
                                    fixed_anything = True
                        except Exception:
                            pass

                # 2. METADATA (Spotify first)
                is_real_spotify = track.spotify_id and len(track.spotify_id) == 22 and not track.spotify_id.startswith("yt_")
                
                if (not track.thumbnail or track.thumbnail == "nebula-default" or not track.release_date) and is_real_spotify:
                    try:
                        sp_data = sp._call_api("track", track.spotify_id)
                        if sp_data:
                            track.duration_ms = sp_data.get("duration_ms", track.duration_ms)
                            track.album = sp_data.get("album", {}).get("name", track.album)
                            track.release_date = sp_data.get("album", {}).get("release_date", track.release_date)
                            imgs = sp_data.get("album", {}).get("images", [])
                            if imgs: track.thumbnail = imgs[0]["url"]
                            fixed_anything = True
                    except: 
                        pass

                # 3. AUDIO DNA (iTunes fallback for analysis)
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

                # Safety: Ensure no infinite loops on un-healable tracks
                if not track.thumbnail: track.thumbnail = "nebula-placeholder"
                if track.duration_ms == 0: track.duration_ms = 180000 
                if track.energy == 0: track.energy = 0.001
                if track.danceability == 0: track.danceability = 0.001
                
                db.commit()
                if fixed_anything:
                    Logger.info("ENRICH", f"Healed track: {track.track_name}")
            
            return True
        except Exception as e:
            Logger.error("ENRICH", f"Batch healing failed: {e}")
            return False
        finally:
            db.close()
