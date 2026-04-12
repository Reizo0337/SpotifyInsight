from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.auth import router as auth_router
from .api.music import router as music_router
from .api.playlists import router as playlists_router
from .db.session import init_db
from .core.logging import Logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    Logger.info("SYSTEM", "Nebula Music Engine initializing...")
    try:
        init_db()
        Logger.info("SYSTEM", "Capa de API ligera lista. Operaciones pesadas delegadas al Worker.")
    except Exception as e:
        Logger.error("SYSTEM", f"Initialization failure: {e}")
    
    yield
    
    # Shutdown logic
    Logger.info("SYSTEM", "Nebula Music Engine powering down.")

app = FastAPI(
    title="Nebula Music API",
    description="Motor de audio para la nueva era de Nebula",
    version="2.1.0",
    lifespan=lifespan
)

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modular Routers (v1)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(music_router, prefix="/api/v1/music", tags=["Music"])
app.include_router(playlists_router, prefix="/api/v1/playlists", tags=["Playlists"])

# Nebula Music API - Core initialized
@app.get("/")
async def root():
    return {
        "app": "Nebula Music",
        "status": "online",
        "version": "2.1.1", # Increment version for reload
        "engine": "Cosmos Core 2.1 (Stability Patch)",
        "philosophy": "SQL-first, Low-latency streaming"
    }
