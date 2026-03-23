import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

def get_auth_manager():
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/api/auth/spotify/callback"),
        scope="user-top-read user-library-read user-read-recently-played"
    )

def get_spotify_client():
    try:
        sp = spotipy.Spotify(auth_manager=get_auth_manager())
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

def get_spotify_client_from_token(token_info):
    """Initializes a Spotify client using a stored token info dictionary."""
    if not token_info: return None
    try:
        # Create an auth manager with the stored token
        auth_manager = SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/api/auth/spotify/callback"),
            scope="user-top-read user-library-read user-read-recently-played"
        )
        # Verify and refresh token if needed
        # auth_manager.get_cached_token = lambda: token_info 
        # Actually SpotifyOAuth handles refreshing if we provide token_info
        sp = spotipy.Spotify(auth=token_info.get("access_token"))
        return sp
    except Exception as e:
        print(f"[SPOTIFY-AUTH] Token setup error: {e}")
        return None
