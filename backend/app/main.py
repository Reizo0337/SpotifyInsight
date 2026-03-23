from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.auth import router as auth_router
from .api.music import router as music_router
from .api.playlists import router as playlists_router
from .api.endpoints import router as legacy_router
from .db.session import init_db
from .services.enrichment_service import start_enrichment_worker

app = FastAPI(
    title="Nebula Music API",
    description="Motor de audio para la nueva era de Nebula",
    version="2.0.0"
)

# Initialize Database and Background Services
@app.on_event("startup")
async def on_startup():
    try:
        init_db()
        # Start background health worker for track metadata
        start_enrichment_worker()
    except Exception as e:
        print(f"Error initializing services: {e}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modular Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(music_router, prefix="/api/music", tags=["Music"])
app.include_router(playlists_router, prefix="/api/playlists", tags=["Playlists"])
app.include_router(legacy_router, prefix="/api", tags=["Legacy"])

@app.get("/")
async def root():
    return {
        "app": "Nebula Music",
        "status": "online",
        "engine": "Cosmos Core 2.0",
        "features": ["Modular Auth", "MySQL Persistent", "Parallel Import"]
    }
