from pydantic import BaseModel

class SyncStatus(BaseModel):
    status: str # "idle", "in_progress", "completed", "error"
    new_tracks: int = 0
    total_library: int = 0
    time_taken: str = "0s"
