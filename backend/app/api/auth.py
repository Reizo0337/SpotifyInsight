from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from ..db.session import get_db
from ..db.models import User
from ..core.auth_utils import get_password_hash, verify_password, create_access_token, get_current_user
from ..core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from pydantic import BaseModel, EmailStr
from typing import Optional
from fastapi.responses import RedirectResponse
from ..core.spotify_auth import get_auth_manager

router = APIRouter()

from ..schemas import UserCreate, Token, UserProfile

@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    
    # Create new user record
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        preferences={}
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Auto-login after registration
    access_token = create_access_token(data={"sub": new_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "preferences": current_user.preferences,
        "spotify_connected": current_user.spotify_token_info is not None
    }

@router.get("/spotify/login")
async def spotify_login(current_user: User = Depends(get_current_user)):
    """Generates the Spotify authorization URL."""
    auth_manager = get_auth_manager()
    # Pass user ID in state to recover context in callback
    auth_url = auth_manager.get_authorize_url(state=str(current_user.id))
    return {"url": auth_url}

@router.get("/spotify/callback")
async def spotify_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handles the Spotify OAuth callback and links the account."""
    auth_manager = get_auth_manager()
    try:
        token_info = auth_manager.get_access_token(code)
        user_id = int(state)
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        user.spotify_token_info = token_info
        
        # Pull profile for metadata
        from ..services.spotify_service import SpotifyService
        sp = SpotifyService(token_info=token_info)
        prof = sp.get_user_profile()
        if prof:
            user.spotify_id = prof["user_id"]
            
        db.commit()
        return RedirectResponse(url="http://localhost:5173/?connected=true")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Spotify link failed: {str(e)}")
