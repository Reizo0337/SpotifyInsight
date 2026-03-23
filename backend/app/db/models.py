from sqlalchemy import Column, String, Integer, Boolean, Float, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
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
    yt_id = Column(String(50), nullable=True)
    stream_url = Column(Text, nullable=True)
    stream_expiry = Column(Float, default=0)
    
    # Audio Features (Spotify)
    danceability = Column(Float, default=0.0)
    energy = Column(Float, default=0.0)
    tempo = Column(Float, default=0.0)
    valence = Column(Float, default=0.0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
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
    added_at = Column(DateTime, default=datetime.utcnow)
    
    playlist = relationship("Playlist", back_populates="tracks")

class Favorite(Base):
    __tablename__ = "favorites"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    spotify_id = Column(String(50), ForeignKey("tracks.spotify_id"), primary_key=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="favorites")

class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    spotify_id = Column(String(50), ForeignKey("tracks.spotify_id"))
    played_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="history")
