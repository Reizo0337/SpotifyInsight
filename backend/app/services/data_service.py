
import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed", "user_tracks.csv")

class DataService:
    @staticmethod
    def load_data():
        if not os.path.exists(DATA_PATH):
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(DATA_PATH)
            # Mapa de columnas antiguas a nuevas
            column_mapping = {
                "Track/Item Name": "track_name",
                "Artist/Detail": "artist",
                "Album": "album",
                "Source": "source"
            }
            df = df.rename(columns=column_mapping)
            
            # Definir columnas técnicas y sus tipos
            float_features = [
                "danceability", "energy", "tempo", "valence", 
                "acousticness", "instrumentalness", "speechiness", "loudness"
            ]
            
            # Inicializar y forzar tipos para evitar errores de "Invalid value for dtype int64"
            for col in float_features:
                if col not in df.columns:
                    df[col] = 0.0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
            
            # Otras columnas necesarias
            for col in ["popularity", "spotify_id", "artist_id", "genre", "key", "mode"]:
                if col not in df.columns:
                    # Inicializamos key/mode como int
                    df[col] = 0 if col in ["popularity", "key", "mode"] else "Unknown"
            
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()

    @staticmethod
    def save_data(df):
        df.to_csv(DATA_PATH, index=False)

    @staticmethod
    def append_new_tracks(new_tracks):
        existing_df = DataService.load_data()
        new_df = pd.DataFrame(new_tracks)
        
        if existing_df.empty:
            combined_df = new_df
        else:
            combined_df = pd.concat([existing_df, new_df]).drop_duplicates(
                subset=["track_name", "artist"], 
                keep="last"
            ).reset_index(drop=True)

        # Fallback: Si hay canciones con 0s (porque Spotify 403 falló), 
        # intentamos el análisis local de preview para las primeras 5 de la lista
        from .audio_analysis_service import AudioAnalysisService
        from .spotify_service import SpotifyService
        
        mask_to_analyze = (combined_df["energy"] == 0) | (combined_df["danceability"] == 0)
        to_analyze = combined_df[mask_to_analyze].head(20)
        
        if not to_analyze.empty:
            print(f"Analyzing {len(to_analyze)} tracks via local audio processing...")
            sp = SpotifyService()
            for idx, row in to_analyze.iterrows():
                # Necesitamos el preview_url
                track_info = sp.sp.track(row["spotify_id"])
                preview_url = track_info.get("preview_url")
                
                # Fallback a iTunes si Spotify no tiene preview
                if not preview_url:
                    preview_url = AudioAnalysisService.get_preview_from_itunes(row["track_name"], row["artist"])
                
                if preview_url:
                    features = AudioAnalysisService.analyze_preview(preview_url)
                    if features:
                        for key, val in features.items():
                            if key in combined_df.columns:
                                combined_df.at[idx, key] = val
            print("Audio analysis pass complete.")

        DataService.save_data(combined_df)
        return combined_df
