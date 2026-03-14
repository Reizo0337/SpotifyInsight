
import asyncio
import pandas as pd
from app.services.data_service import DataService
from app.services.audio_analysis_service import AudioAnalysisService
from app.services.spotify_service import SpotifyService
import os

async def heal_all():
    print("Starting Mega-Heal process...")
    df = DataService.load_data()
    
    if df.empty:
        print("No data found.")
        return

    mask_to_analyze = (df["energy"] == 0) | (df["danceability"] == 0)
    to_analyze = df[mask_to_analyze]
    
    total = len(to_analyze)
    print(f"Found {total} tracks to enrich.")
    
    if total == 0:
        print("All tracks are already enriched!")
        return

    sp = SpotifyService()
    count = 0
    
    # Process in chunks of 5 to avoid overloading but keep moving
    for idx, row in to_analyze.iterrows():
        print(f"[{count+1}/{total}] Processing: {row['track_name']} - {row['artist']}")
        
        try:
            # 1. Get preview URL
            # We fetch track info to get the preview_url
            track_info = sp.sp.track(row["spotify_id"])
            preview_url = track_info.get("preview_url")
            
            if not preview_url:
                preview_url = AudioAnalysisService.get_preview_from_itunes(row["track_name"], row["artist"])
            
            if preview_url:
                features = AudioAnalysisService.analyze_preview(preview_url)
                if features:
                    for key, val in features.items():
                        if key in df.columns:
                            df.at[idx, key] = val
                    print("  - Success!")
                else:
                    print("  - Analysis failed.")
            else:
                print("  - No preview found.")
        except Exception as e:
            print(f"  - Error: {e}")
        
        count += 1
        
        # Save every 5 tracks just in case
        if count % 5 == 0:
            DataService.save_data(df)
            print("--- Progress saved ---")

    DataService.save_data(df)
    print(f"Finished! {count} tracks processed.")

if __name__ == "__main__":
    asyncio.run(heal_all())
