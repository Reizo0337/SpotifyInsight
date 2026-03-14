
import asyncio
import pandas as pd
from app.services.data_service import DataService
from app.services.audio_analysis_service import AudioAnalysisService
from app.services.spotify_service import SpotifyService
import os

async def heal_all():
    print("Starting Mega-Heal process for Track Library...")
    # We heal the LIBRARY, not the user history
    df = DataService.load_library()
    
    if df.empty:
        print("Library is empty.")
        return

    mask_to_analyze = (df["energy"] == 0) | (df["danceability"] == 0)
    to_analyze = df[mask_to_analyze]
    
    total = len(to_analyze)
    print(f"Found {total} tracks in library to enrich.")
    
    if total == 0:
        print("All tracks in library are already enriched!")
        return

    sp = SpotifyService()
    count = 0
    
    for idx, row in to_analyze.iterrows():
        print(f"[{count+1}/{total}] Analyzing: {row['track_name']} - {row['artist']}")
        
        try:
            # 1. Try Spotify Official Features first
            features = None
            try:
                af = sp.sp.audio_features([row["spotify_id"]])
                if af and af[0]:
                    features = {
                        "danceability": af[0].get("danceability"),
                        "energy": af[0].get("energy"),
                        "tempo": af[0].get("tempo"),
                        "valence": af[0].get("valence"),
                        "acousticness": af[0].get("acousticness"),
                        "instrumentalness": af[0].get("instrumentalness"),
                        "speechiness": af[0].get("speechiness"),
                        "loudness": af[0].get("loudness"),
                        "key": af[0].get("key"),
                        "mode": af[0].get("mode")
                    }
                    print("  - Spotify features found!")
            except Exception:
                pass

            # 2. Fallback to Local Audio Analysis if Spotify features unavailable
            if not features:
                track_info = sp.sp.track(row["spotify_id"])
                preview_url = track_info.get("preview_url")
                
                if not preview_url:
                    preview_url = AudioAnalysisService.get_preview_from_itunes(row["track_name"], row["artist"])
                
                if preview_url:
                    features = AudioAnalysisService.analyze_preview(preview_url)
                    if features:
                        print("  - Local analysis success!")
            
            if features:
                for key, val in features.items():
                    if key in df.columns:
                        df.at[idx, key] = val
            else:
                print("  - No data found for this track.")
        except Exception as e:
            print(f"  - Error: {e}")
        
        count += 1
        
        # Save progress
        if count % 5 == 0:
            DataService.save_library(df)
            print("--- Library progress saved ---")

    DataService.save_library(df)
    print(f"Finished! {count} tracks updated in library.")

if __name__ == "__main__":
    asyncio.run(heal_all())
