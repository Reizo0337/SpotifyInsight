from pydantic import BaseModel
from typing import Optional

class TrackBase(BaseModel):
    spotify_id: str
    track_name: str
    artist: str
    artist_id: Optional[str] = None
    album: Optional[str] = None
    popularity: Optional[int] = 0
    genre: Optional[str] = "Unknown"
    thumbnail: Optional[str] = None
    duration_ms: Optional[int] = 0

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

class RecommendationRequest(BaseModel):
    mode: str = "vibe" # "vibe", "discovery", "similar"
    limit: int = 10
    song_query: Optional[str] = None
