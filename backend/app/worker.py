import sys
import time
import sys, time, uuid, concurrent.futures
from datetime import datetime, timezone
from .db.session import SessionLocal
from .db.models import Track, User, Job, Playlist, PlaylistTrack, History
from .services.ytmusic_service import YTMusicService
from .services.spotify_service import SpotifyService
from .services.playlist_scraper import scrape_playlist_tracks
from .core.logging import Logger

MAX_PARALLEL_ENRICHMENT = 8

def process_jobs():
    """Main job loop: designed to be called by a task scheduler or demand."""
    db = SessionLocal()
    try:
        # 1. Claim Job (Atomic assignment)
        job = db.query(Job).filter(
            (Job.status == "queued") | (Job.status == "retrying")
        ).order_by(Job.created_at.asc()).first()
        
        if not job: return False

        job.status = "assigned"
        job.heartbeat_at = datetime.now(timezone.utc)
        db.commit()

        # 2. Start Processing
        Logger.info("WORKER", f"Processing job {job.id} (Attempt {job.retry_count + 1})")
        job.status = "processing"
        db.commit()

        if job.type == "playlist_import":
            handle_playlist_import(db, job)
        elif job.type == "library_sync":
            handle_library_sync(db, job)
        elif job.type == "recommendations":
            handle_recommendations(db, job)
        else:
            job.status = "failed"
            job.error = "Unknown job type"
            db.commit()
            
        return True

    except Exception as e:
        Logger.error("WORKER", f"Worker loop internal error: {e}")
        return False
    finally:
        db.close()

def handle_recommendations(db, job):
    """Heavy IA music analysis and cross-reference."""
    try:
        from .services.recommendation_service import RecommendationService
        from sqlalchemy import func
        limit = (job.result or {}).get("limit", 20)
        
        # 1. Get user context
        history = db.query(Track).join(History).filter(History.user_id == job.user_id).order_by(History.played_at.desc()).limit(100).all()
        candidates = db.query(Track).order_by(func.random()).limit(150).all()
        
        # 2. External seeds (Spotify)
        spotify_recs = []
        user = db.query(User).filter(User.id == job.user_id).first()
        if user and user.spotify_token_info:
            sp = SpotifyService(token_info=user.spotify_token_info)
            recent_ids = [t.spotify_id for t in history[:5]]
            if recent_ids:
                spotify_recs = sp.get_recommendations_from_spotify(recent_ids, limit)
        
        # 3. Hybrid Analysis (Heartbeat check)
        job.message = "Calculando resonancia musical..."
        job.heartbeat_at = datetime.now(timezone.utc)
        db.commit()
        
        recs = RecommendationService.get_recommendations(history, candidates, limit, spotify_recs)
        
        # 4. Serialize result IDs
        # We store just the IDs to keep Job record light
        results = [r.spotify_id if hasattr(r, "spotify_id") else r.get("spotify_id") for r in recs if r]
        
        job.status = "completed"
        job.progress = 100
        job.message = "Recomendaciones generadas."
        job.result = {"tracks": results}
        db.commit()

    except Exception as e:
        db.rollback()
        job.status = "failed"
        job.error = str(e)
        db.commit()

def handle_library_sync(db, job):
    """Deep synchronization of Spotify Library and History."""
    try:
        user = db.query(User).filter(User.id == job.user_id).first()
        if not user or not user.spotify_token_info:
            raise Exception("No active Spotify uplink.")

        sp = SpotifyService(token_info=user.spotify_token_info)
        
        # Helper for progress
        def tick(msg, prog):
            job.message = msg
            job.progress = prog
            job.heartbeat_at = datetime.now(timezone.utc)
            db.commit()

        tick("Capturando 'Liked Songs' de Spotify...", 10)
        
        # 1. Sync Liked Songs
        liked = sp.sync_user_library() # Returns list of tracks
        total_liked = len(liked)
        tick(f"Detectadas {total_liked} favoritas. Sincronizando metadatos...", 20)
        
        from .db.models import Favorite
        processed = 0
        new_track_count = 0
        
        for t in liked:
            sid = t["id"]
            track = db.query(Track).filter(Track.spotify_id == sid).first()
            if not track:
                album = t.get("album", {})
                track = Track(
                    spotify_id=sid,
                    track_name=t.get("name", "Unknown"),
                    artist=t.get("artists", [{}])[0].get("name", "Unknown"),
                    album=album.get("name", "Unknown"),
                    thumbnail=album.get("images", [{}])[0].get("url", ""),
                    duration_ms=t.get("duration_ms", 0)
                )
                db.add(track)
                db.flush()
                new_track_count += 1
            
            # Ensure in Favorites
            is_fav = db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.spotify_id == sid).first()
            if not is_fav:
                db.add(Favorite(user_id=user.id, spotify_id=sid))
            
            processed += 1
            if processed % 15 == 0:
                tick(f"Sincronizando favoritas: {processed}/{total_liked}...", 20 + int((processed / total_liked) * 40))

        db.commit()

        # 2. Sync Recent History
        tick("Revisando viajes musicales recientes (Spotify History)...", 70)
        recent = sp._call_api("current_user_recently_played", limit=50)
        if recent and "items" in recent:
            for item in recent["items"]:
                t = item.get("track")
                if t:
                    sid = t["id"]
                    if not db.query(Track).filter(Track.spotify_id == sid).first():
                        db.add(Track(spotify_id=sid, track_name=t["name"], artist=t["artists"][0]["name"]))
                    db.add(History(user_id=user.id, spotify_id=sid))
        
        db.commit()

        # 3. Queue Audio Features (DNA) for new tracks
        if new_track_count > 0:
            tick(f"Analizando biometría musical ({new_track_count} nuevos tracks)...", 90)
            # Find tracks with energy=0 to enrich
            pending = db.query(Track).filter(Track.energy == 0).limit(100).all()
            # ONLY include IDs that look like valid Spotify IDs (22 chars)
            ids = [t.spotify_id for t in pending if t.spotify_id and len(t.spotify_id) == 22]
            if ids:
                features = sp.get_audio_features(ids)
                for i, f in enumerate(features):
                    target = db.query(Track).filter(Track.spotify_id == ids[i]).first()
                    if target and f:
                        target.danceability = f.get("danceability", 0)
                        target.energy = f.get("energy", 0)
                        target.tempo = f.get("tempo", 0)
                        target.valence = f.get("valence", 0)
                db.commit()

        job.status = "completed"
        job.progress = 100
        job.message = "Biblioteca sincronizada y sanada."
        db.commit()

    except Exception as e:
        db.rollback()
        job.status = "failed"
        job.error = str(e)
        db.commit()

def handle_playlist_import(db, job):
    try:
        data = job.result or {}
        playlist_id = data.get("playlist_id")
        user_id = job.user_id
        pl_uuid = data.get("target_playlist_id") or str(uuid.uuid4())

        # Update heartbeat periodically
        def tick(msg, prog):
            job.message = msg
            job.progress = prog
            job.heartbeat_at = datetime.now(timezone.utc)
            db.commit()

        tick("Iniciando escaneo de señales...", 10)
        
        # [SCRAPE PHASE]
        scraped = scrape_playlist_tracks(playlist_id)
        if not scraped: raise Exception("No signals found at URL.")
        
        tick(f"Mapeando {len(scraped)} tracks...", 20)

        # [PERSISTENCE PHASE]
        # Ensure Playlist exists
        pl = db.query(Playlist).filter(Playlist.id == pl_uuid).first()
        if not pl:
            pl = Playlist(id=pl_uuid, name=data.get("name", "Nebula Import"), user_id=user_id)
            db.add(pl)
            db.flush()

        # [FAN-OUT PHASE] Parallel YouTube/Metadata Healing
        total = len(scraped)
        processed = 0
        
        # Parallel Enrichment Execution
        def heal_track(t_data):
            # Create local session for thread safety
            t_db = SessionLocal()
            try:
                tid = t_data.get("spotify_id")
                track = t_db.query(Track).filter(Track.spotify_id == tid).first()
                if not track:
                    track = Track(
                        spotify_id=tid,
                        track_name=t_data["track_name"],
                        artist=t_data["artist"],
                        thumbnail=t_data.get("thumbnail", ""),
                        duration_ms=t_data.get("duration_ms", 0)
                    )
                    t_db.add(track)
                    t_db.flush()

                # Basic record creation (Lightweight)
                if not track:
                    track = Track(
                        spotify_id=tid,
                        track_name=t_data["track_name"],
                        artist=t_data["artist"],
                        thumbnail=t_data.get("thumbnail", ""),
                        duration_ms=t_data.get("duration_ms", 0)
                    )
                    t_db.add(track)
                    t_db.flush()

                # Link association
                link = t_db.query(PlaylistTrack).filter(
                    PlaylistTrack.playlist_id == pl_uuid, 
                    PlaylistTrack.spotify_id == tid
                ).first()
                if not link:
                    t_db.add(PlaylistTrack(playlist_id=pl_uuid, spotify_id=tid))
                
                t_db.commit()
                return True
            except Exception as e:
                t_db.rollback()
                return False
            finally:
                t_db.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_PARALLEL_ENRICHMENT) as executor:
            futures = [executor.submit(heal_track, t) for t in scraped]
            for future in concurrent.futures.as_completed(futures):
                processed += 1
                if processed % 5 == 0:
                    prog = min(20 + int((processed / total) * 75), 95)
                    tick(f"Sincronizando: {processed}/{total} tracks...", prog)

        # [DONE]
        job.status = "completed"
        job.progress = 100
        job.message = "Sincronización galáctica finalizada."
        job.result = {**data, "playlist_id": pl_uuid, "count": total}
        db.commit()

    except Exception as e:
        db.rollback()
        if job.retry_count < 3:
            job.status = "retrying"
            job.retry_count += 1
            job.message = f"Reintentando por error técnico... ({job.retry_count})"
        else:
            job.status = "failed"
            job.error = str(e)
            job.message = "Error crítico tras múltiples intentos."
        db.commit()

if __name__ == "__main__":
    from .services.enrichment_service import EnrichmentService
    Logger.info("WORKER", "Samurái Nebula en modo Patrulla... (Guardia Activa)")
    try:
        while True:
            # 1. Check for high-priority user jobs
            has_jobs = process_jobs()
            
            # 2. If idle, do some background healing (one batch of 5 tracks)
            if not has_jobs:
                # Use a lightweight enrichment check
                was_healed = EnrichmentService.heal_small_batch()
                
                # 3. Dynamic sleep logic
                if not was_healed:
                    time.sleep(10) # Heavy sleep if totally idle
                else:
                    time.sleep(2)  # Short sleep if we are in a healing streak
            else:
                # If we processed a job, check again immediately
                continue
    except KeyboardInterrupt:
        Logger.info("WORKER", "Samurái retirándose a descansar.")
