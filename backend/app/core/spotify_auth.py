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
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8000/api/auth/spotify/callback"),
        scope="user-top-read user-library-read user-read-recently-played playlist-read-private playlist-read-collaborative"
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
    """Initializes a Spotify client with support for automatic token refreshing."""
    if not token_info: return None
    try:
        auth_manager = get_auth_manager()
        # The Spotify client will use the auth_manager to get the current token, 
        # refreshing it if necessary using the information in token_info.
        # We manually check/refresh here once to be safe before returning the client.
        if auth_manager.is_token_expired(token_info):
            token_info = auth_manager.refresh_access_token(token_info.get("refresh_token"))
            
        sp = spotipy.Spotify(auth=token_info.get("access_token"))
        return sp, token_info # Return updated token_info in case it was refreshed
    except Exception as e:
        print(f"[SPOTIFY-AUTH] Token setup error: {e}")
        return None, None
