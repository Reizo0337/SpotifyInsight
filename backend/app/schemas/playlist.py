from pydantic import BaseModel
from typing import Optional, List

class PlaylistBase(BaseModel):
    id: str
    name: str
    is_public: bool = True
    tracks: List[str] = []
    thumbnail: Optional[str] = None
    
    model_config = {"from_attributes": True}

class PlaylistCreate(BaseModel):
    name: str
    is_public: bool = True

class PlaylistImport(BaseModel):
    url: str
    name: str
    target_playlist_id: Optional[str] = None
