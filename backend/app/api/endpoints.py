from fastapi import APIRouter, HTTPException
from ..services.spotify_service import SpotifyService
from ..services.data_service import DataService
from ..services.analysis_service import AnalysisService
from ..services.recommendation_service import RecommendationService

router = APIRouter()

@router.get("/sync")
async def sync_data():
    try:
        spotify = SpotifyService()
        top_tracks = spotify.get_top_tracks_with_features()
        recent_tracks = spotify.get_recently_played_with_features()
        
        all_new_tracks = top_tracks + recent_tracks
        df = DataService.append_new_tracks(all_new_tracks)
        
        return {"status": "success", "tracks_synced": len(all_new_tracks), "total_tracks": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis")
async def get_analysis():
    df = DataService.load_data()
    if df.empty:
        return {"status": "no_data", "message": "No data available. Please sync first."}
    
    stats = AnalysisService.get_summary_stats(df)
    return stats

@router.get("/recommendations")
async def get_recommendations(limit: int = 10, song: str = None):
    df = DataService.load_data()
    spotify = SpotifyService()
    
    if not spotify.is_connected():
        raise HTTPException(status_code=503, detail="Spotify service is not available. Please check your internet connection or credentials.")

    # Si el usuario busca una canción específica
    if song:
        target_track = spotify.search_track(song)
        if not target_track:
            raise HTTPException(status_code=404, detail="Song not found on Spotify")
            
        # Obtener IDs de los gustos del usuario del dataset local
        user_taste_ids = []
        if not df.empty and "spotify_id" in df.columns:
            user_taste_ids = df[df["spotify_id"] != "0"]["spotify_id"].dropna().tail(10).tolist()
        
        recs = spotify.get_recommendations_weighted(target_track, user_taste_ids, limit=limit)
        return {
            "based_on": target_track,
            "weight": "80% song / 20% your taste",
            "recommendations": recs
        }

    # Comportamiento original si no hay 'song'
    if df.empty:
        return {"status": "no_data", "message": "No data available. Please sync first."}
    
    # Try local recommendation engine first
    recs = RecommendationService.get_recommendations(df, n_recommendations=limit)
    
    # If local engine fails (due to lack of audio features), fallback to Spotify API
    if not recs:
        try:
            spotify = SpotifyService()
            # Try Track Seeds first
            if "spotify_id" in df.columns:
                seed_ids = df[df["spotify_id"] != "0"]["spotify_id"].dropna().tail(5).tolist()
                recs = spotify.get_recommendations_from_spotify(seed_ids, limit=limit)
                
            # If Track Seeds also fails (404), try Artist Seeds
            if not recs and "artist_id" in df.columns:
                artist_seeds = df[df["artist_id"].notna()]["artist_id"].tail(5).tolist()
                try:
                    results = spotify.sp.recommendations(seed_artists=artist_seeds, limit=limit)
                    recs = [{
                        "track_name": t["name"],
                        "artist": t["artists"][0]["name"],
                        "album": t["album"]["name"],
                        "popularity": t.get("popularity", 0),
                        "spotify_id": t["id"]
                    } for t in results["tracks"]]
                except Exception:
                    pass
        except Exception:
            recs = []
            
    return recs

@router.get("/analyze-track")
async def analyze_track(song: str, artist: str = ""):
    spotify = SpotifyService()
    if not spotify.is_connected():
        raise HTTPException(status_code=503, detail="Spotify disconnected")

    # 1. Search for track to get preview_url
    query = f"{song} {artist}"
    track = spotify.search_track(query)
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    from ..services.audio_analysis_service import AudioAnalysisService
    preview_url = track.get("preview_url")
    
    # Si Spotify no tiene preview, intentamos iTunes
    if not preview_url:
        print(f"Spotify preview missing for {track['name']}, trying iTunes...")
        preview_url = AudioAnalysisService.get_preview_from_itunes(track["name"], track["artist"])

    if not preview_url:
        return {
            "error": "No preview available for this track on Spotify or iTunes.",
            "suggestions": [f"Try searching for a different version of {song}", "Check if the song is available in your region"]
        }

    # 2. Analyze audio
    analysis = AudioAnalysisService.analyze_preview(preview_url)

    if not analysis:
        raise HTTPException(status_code=500, detail="Could not analyze audio preview")

    return {
        "song_name": track["name"],
        "artist": track["artist"],
        "spotify_id": track["id"],
        **analysis
    }

@router.get("/user-profile")
async def get_user_profile():
    df = DataService.load_data()
    if df.empty:
        return {"status": "no_data", "message": "No data available. Please sync first."}
    
    features = ["danceability", "energy", "tempo", "valence", "popularity"]
    # Ensure numeric
    temp_df = df.copy()
    for f in features:
        if f in temp_df.columns:
            temp_df[f] = pd.to_numeric(temp_df[f], errors='coerce').fillna(0)
            
    profile = temp_df[features].mean().to_dict()
    
    return {
        "user_features": profile,
        "total_tracks_analyzed": len(df)
    }
