"""
YTMusicService: Uses yt-dlp to search YouTube Music and extract
a direct audio stream URL without downloading any files.
"""
import yt_dlp
import traceback
from ..core.logging import Logger


def _quiet_ydl_opts(extra: dict = {}) -> dict:
    base = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "noplaylist": True,
        "cookiesfrombrowser": ("brave",),
    }
    base.update(extra)
    return base


def _get_info_resilient(query: str, extra_opts: dict = {}) -> dict | None:
    """Extraer info de YoutubeDL manejando fallos de cookies por base de datos bloqueada."""
    opts = _quiet_ydl_opts(extra_opts)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(query, download=False)
    except Exception as e:
        err_str = str(e).lower()
        if "could not copy" in err_str or "cookie" in err_str or "locked" in err_str:
            Logger.warning("YTMUSIC", "Base de datos de cookies bloqueada (Brave abierto). Reintentando sin cookies...")
            if "cookiesfrombrowser" in opts:
                del opts["cookiesfrombrowser"]
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(query, download=False)
            except Exception as e2:
                Logger.error("YTMUSIC", f"Fallo definitivo en extracción: {e2}")
                return None
        Logger.error("YTMUSIC", f"Error en extracción yt-dlp: {e}")
        return None


class YTMusicService:

    @staticmethod
    def search_and_get_stream(track_name: str, artist: str, video_id: str = None) -> dict | None:
        """
        Searches YouTube Music for `artist - track_name` and returns
        a direct audio stream URL (no download).
        If video_id is provided, it attempts to get the stream for that ID directly.
        """
        # 1. OPTIMIZED PATH: Direct ID
        if video_id:
            Logger.info("YTMUSIC", f"Direct stream request for ID: {video_id}")
            info_dict = _get_info_resilient(f"https://www.youtube.com/watch?v={video_id}", {"format": "bestaudio/best"})
            if info_dict and info_dict.get("url"):
                return {
                    "stream_url": info_dict["url"],
                    "title": info_dict.get("title", f"{artist} - {track_name}"),
                    "thumbnail": info_dict.get("thumbnail", ""),
                    "duration": info_dict.get("duration", 0),
                    "view_count": info_dict.get("view_count", 0),
                    "video_id": video_id,
                }

        # 2. SEARCH PATH: String fallback
        effective_artist = artist if (artist and artist.lower() != "unknown") else ""
        
        # Tiered search strategy for maximum resilience
        queries = []
        if effective_artist:
            queries.append(f"ytsearch5:{effective_artist} {track_name} official audio")
            queries.append(f"ytsearch5:{effective_artist} - {track_name} topic")
            queries.append(f"ytsearch5:{effective_artist} {track_name}")
        queries.append(f"ytsearch5:{track_name} official audio")
        queries.append(f"ytsearch5:{track_name}")
        
        ydl_opts = _quiet_ydl_opts({
            "format": "bestaudio/best",
            "noplaylist": True,
            "source_address": "0.0.0.0" # Force IPv4 for stability
        })

        for query in queries:
            Logger.info("YTMUSIC", f"Streaming search for query: {query}")
            info_dict = _get_info_resilient(query, {"format": "bestaudio/best", "source_address": "0.0.0.0"})
            
            if not info_dict or 'entries' not in info_dict or len(info_dict['entries']) == 0:
                continue
            
            for entry in info_dict['entries']:
                if not entry: continue
                stream_url = entry.get("url")
                if stream_url:
                    Logger.success("YTMUSIC", f"Stream found: {entry.get('title')} (ID: {entry.get('id')})")
                    return {
                        "stream_url": stream_url,
                        "title": entry.get("title", f"{artist} - {track_name}"),
                        "thumbnail": entry.get("thumbnail", ""),
                        "duration": entry.get("duration", 0),
                        "view_count": entry.get("view_count", 0),
                        "video_id": entry.get("id"),
                    }
                
        return None

    @staticmethod
    def search_and_get_id(track_name: str, artist: str) -> str | None:
        """
        Quickly resolves a YouTube Video ID for a track name and artist.
        """
        data = YTMusicService.search_and_get_stream(track_name, artist)
        return data.get("video_id") if data else None

    @staticmethod
    def search_tracks(query: str, limit: int = 10) -> list:
        """
        Searches YouTube for tracks matching the query.
        Returns a list of metadata dicts.
        """
        search_query = f"ytsearch{limit}:{query}"
        Logger.info("YTMUSIC", f"Direct search: {search_query}")
        
        ydl_opts = _quiet_ydl_opts({
            "extract_flat": True,
        })
        
        results = []
        info_dict = _get_info_resilient(search_query, {"extract_flat": True})
        
        if not info_dict or 'entries' not in info_dict:
            return []
        
        for entry in info_dict['entries']:
            if not entry: continue
            title = entry.get("title", "Unknown")
            uploader = entry.get("uploader", "Unknown Channel")
            
            # Split title if it contains " - "
            artist = uploader
            track_name = title
            if " - " in title:
                parts = title.split(" - ", 1)
                artist = parts[0].strip()
                track_name = parts[1].strip()
            
            results.append({
                "id": entry.get("id"),
                "track_name": track_name,
                "artist": artist,
                "album": uploader,
                "thumbnail": entry.get("thumbnail") or (entry.get("thumbnails", [{}])[0].get("url") if entry.get("thumbnails") else None),
                "duration_ms": (entry.get("duration", 0) or 0) * 1000,
                "spotify_id": f"yt_{entry.get('id')}"
            })
        return results
