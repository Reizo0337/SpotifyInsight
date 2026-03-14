
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
            
            # Columnas mínimas requeridas para que no sea considerado "legacy"
            required_columns = ["track_name", "artist", "danceability", "energy"]
            
            # Si faltan columnas técnicas, las inicializamos en 0 en lugar de descartar todo
            for col in ["danceability", "energy", "tempo", "valence", "popularity", "spotify_id"]:
                if col not in df.columns:
                    df[col] = 0
            
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
            # We use keep='last' to ensure new data (with updated features/genres) 
            # overwrites old incomplete data for the same track.
            combined_df = pd.concat([existing_df, new_df]).drop_duplicates(
                subset=["track_name", "artist"], 
                keep="last"
            )
        
        DataService.save_data(combined_df)
        return combined_df
