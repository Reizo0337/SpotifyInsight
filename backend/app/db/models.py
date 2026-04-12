from sqlalchemy import Column, String, Integer, BigInteger, Boolean, Float, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Spotify Integration
    spotify_token_info = Column(JSON, nullable=True) # {access, refresh, expires...}
    spotify_id = Column(String(100), unique=True, nullable=True)
    preferences = Column(JSON, default={}) # survey results etc.
    
    playlists = relationship("Playlist", back_populates="owner")
    history = relationship("History", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")

class Track(Base):
    """Rich central track repository."""
    __tablename__ = "tracks"
    spotify_id = Column(String(50), primary_key=True, index=True)
    track_name = Column(String(255), nullable=False)
    artist = Column(String(255), index=True)
    album = Column(String(255))
    thumbnail = Column(String(512))
    duration_ms = Column(Integer, default=0)
    popularity = Column(Integer, default=0)
    view_count = Column(BigInteger, default=0) # Supports billions of views (Rihanna-ready)
    yt_id = Column(String(50), nullable=True)
    stream_url = Column(Text, nullable=True)
    stream_expiry = Column(Float, default=0)
    
    # Audio Features (Spotify)
    danceability = Column(Float, default=0.0)
    energy = Column(Float, default=0.0)
    tempo = Column(Float, default=0.0)
    valence = Column(Float, default=0.0)
    genres = Column(JSON, nullable=True)
    release_date = Column(String(50), nullable=True)
    
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Store JSON array of spotify_ids for tracks
    # This simplifies things vs a join table for now if we want to keep current logic
    # But a join table is better for SQL. Let's do it right.
    owner = relationship("User", back_populates="playlists")
    tracks = relationship("PlaylistTrack", back_populates="playlist")

class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    id = Column(Integer, primary_key=True)
    playlist_id = Column(String(50), ForeignKey("playlists.id"))
    spotify_id = Column(String(50), ForeignKey("tracks.spotify_id"))
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    playlist = relationship("Playlist", back_populates="tracks")

class Favorite(Base):
    __tablename__ = "favorites"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    spotify_id = Column(String(50), ForeignKey("tracks.spotify_id"), primary_key=True)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="favorites")

class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    spotify_id = Column(String(50), ForeignKey("tracks.spotify_id"))
    played_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="history")

class Job(Base):
    """Asynchronous job tracking for heavy tasks with high observability."""
    __tablename__ = "jobs"
    id = Column(String(50), primary_key=True) # UUID
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String(50)) # e.g., 'playlist_import'
    
    # States: queued, assigned, processing, retrying, completed, failed, cancelled
    status = Column(String(20), default="queued") 
    progress = Column(Integer, default=0) # 0-100
    message = Column(String(255), nullable=True) 
    
    result = Column(JSON, nullable=True) 
    error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    heartbeat_at = Column(DateTime, nullable=True) # Last time worker was alive
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
