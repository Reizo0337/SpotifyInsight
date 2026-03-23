import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

def get_spotify_client():
    # ... existing OAuth client
    try:
        sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                redirect_uri="http://127.0.0.1:8080/callback",
                scope="user-top-read user-library-read user-read-recently-played playlist-read-private playlist-read-collaborative user-follow-read user-read-playback-state user-read-currently-playing user-modify-playback-state"
            )
        )
        return sp
    except Exception as e:
        print(f"[SPOTIFY-AUTH] Setup error: {e}")
        return None

def get_spotify_public_client():
    """Returns a client for public endpoints using Client Credentials flow."""
    try:
        sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
            )
        )
        return sp
    except Exception as e:
        print(f"[SPOTIFY-AUTH] Public setup error: {e}")
        return None
