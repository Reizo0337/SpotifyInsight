from pydantic import BaseModel
from typing import List, Optional

class Track(BaseModel):
    track_name: str
    artist: str
    album: str
    popularity: int
    danceability: float
    energy: float
    tempo: float
    valence: float
    acousticness: float
    instrumentalness: float
    speechiness: float

class UserProfile(BaseModel):
    user_features: dict
    total_tracks_analyzed: int

class AnalysisSummary(BaseModel):
    total_tracks: int
    avg_popularity: float
    avg_danceability: float
    avg_energy: float
    top_artists: dict
    avg_tempo: float
    avg_valence: float
