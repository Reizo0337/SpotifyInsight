"""
playlist_scraper.py - Scrapes track list from a public Spotify playlist page.

This acts as a fallback when the Spotify Web API refuses access (403) to
a playlist's track endpoint (i.e., the user is not the owner/collaborator).

Strategy:
  1. Fetch the Spotify embed page (https://open.spotify.com/embed/playlist/{id})
  2. Parse the __NEXT_DATA__ JSON blob embedded in the page
  3. Extract track title + artist from the 'trackList' field
  4. Return list of dicts: {track_name, artist, spotify_id}
"""

import re
import json
import requests
from ..core.logging import Logger

SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_playlist_tracks(playlist_id: str) -> list[dict] | None:
    """
    Scrape track names+artists from Spotify's public embed page.
    Returns list of {track_name, artist, spotify_id} or None on failure.
    """
    url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    try:
        res = requests.get(url, headers=SCRAPE_HEADERS, timeout=10)
        if res.status_code != 200:
            Logger.warning("SCRAPER", f"Embed page returned {res.status_code}")
            return None

        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            res.text,
            re.DOTALL,
        )
        if not match:
            Logger.warning("SCRAPER", "Could not find __NEXT_DATA__ in embed page")
            return None

        data = json.loads(match.group(1))

        # Navigate to the track list
        track_list = (
            data.get("props", {})
            .get("pageProps", {})
            .get("state", {})
            .get("data", {})
            .get("entity", {})
            .get("trackList", [])
        )

        if not track_list:
            Logger.warning("SCRAPER", "trackList was empty in embed JSON")
            return None

        tracks = []
        for t in track_list:
            title = t.get("title", "").strip()
            artist = t.get("subtitle", "").strip()
            uid = t.get("uid", "")  # Spotify track ID is embedded in uid

            # uid format is often "spotify:track:<id>" or just the id
            spotify_id = uid.split(":")[-1] if uid else None

            if title:
                tracks.append({
                    "track_name": title,
                    "artist": artist,
                    "spotify_id": spotify_id,
                    # thumbnail / album will be enriched later via Spotify search
                    "thumbnail": None,
                    "album": "Unknown",
                    "duration_ms": 0,
                    "popularity": 0,
                })

        Logger.info("SCRAPER", f"Scraped {len(tracks)} tracks for playlist {playlist_id}")
        return tracks

    except Exception as e:
        Logger.error("SCRAPER", f"Scraping failed for {playlist_id}: {e}")
        return None
