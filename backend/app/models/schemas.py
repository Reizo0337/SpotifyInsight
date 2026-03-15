from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class TrackBase(BaseModel):
    spotify_id: str
    track_name: str
    artist: str
    artist_id: Optional[str] = None
    album: Optional[str] = None
    popularity: Optional[int] = 0
    genre: Optional[str] = "Unknown"

class TrackFeatures(TrackBase):
    danceability: float = 0.0
    energy: float = 0.0
    tempo: float = 0.0
    valence: float = 0.0
    acousticness: float = 0.0
    instrumentalness: float = 0.0
    speechiness: float = 0.0
    loudness: float = 0.0
    key: int = 0
    mode: int = 0

class UserProfile(BaseModel):
    user_id: str
    user_name: str
    stats: Dict[str, Any]

class RecommendationRequest(BaseModel):
    mode: str = "vibe" # "vibe", "discovery", "similar"
    limit: int = 10
    song_query: Optional[str] = None

class SyncStatus(BaseModel):
    status: str
    new_tracks: int
    total_library: int
    time_taken: str
