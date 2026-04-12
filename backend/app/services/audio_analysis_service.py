import requests
import io
import os
import time
import traceback
import av
import numpy as np
import librosa
import uuid

class AudioAnalysisService:
    @staticmethod
    def get_preview_from_itunes(song, artist):
        """
        Fallback to iTunes API to get a 30s preview URL.
        """
        try:
            query = f"{song} {artist}"
            url = "https://itunes.apple.com/search"
            params = {"term": query, "limit": 3, "media": "music"}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    for res in results:
                        if res.get("previewUrl"):
                            return res.get("previewUrl")
        except Exception:
            pass
        return None

    @staticmethod
    def get_itunes_metadata(song, artist):
        """
        Autonomous fallback to fetch popularity and genre from iTunes.
        """
        try:
            query = f"{song} {artist}"
            url = "https://itunes.apple.com/search"
            params = {"term": query, "limit": 10, "media": "music"}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    top = results[0]
                    return {
                        "genre": top.get("primaryGenreName", "Unknown"),
                        "popularity": 60 + (10 if "contentAdvisoryRating" in top else 0),
                        "thumbnail": top.get("artworkUrl100")
                    }
        except Exception:
            pass
        return {"genre": "Unknown", "popularity": 0, "thumbnail": None}

    @staticmethod
    def decode_with_av(temp_path):
        """
        Decodes audio using PyAV (FFmpeg based) and returns (y, sr)
        """
        container = av.open(temp_path)
        stream = container.streams.audio[0]
        resampler = av.AudioResampler(format='s16', layout='mono', rate=22050)
        
        samples = []
        for frame in container.decode(stream):
            frame.pts = None
            resampled_frames = resampler.resample(frame)
            for rf in resampled_frames:
                samples.append(np.frombuffer(rf.planes[0], dtype=np.int16))
        
        if not samples:
            container.close()
            return None, None
            
        y = np.concatenate(samples).astype(np.float32) / 32768.0
        container.close()
        return y, 22050

    @staticmethod
    def analyze_preview(preview_url):
        """
        Downloads a 30s preview and extracts audio features using librosa.
        """
        t_start = time.time()
        if not preview_url:
            return None

        temp_path = None
        try:
            response = requests.get(preview_url, timeout=10)
            if response.status_code != 200:
                return None

            ext = ".mp3"
            if ".m4a" in preview_url.lower() or "aac" in preview_url.lower():
                ext = ".m4a"
            
            temp_filename = f"temp_preview_{uuid.uuid4()}{ext}"
            temp_path = os.path.join(os.getcwd(), temp_filename)
            
            with open(temp_path, "wb") as f:
                f.write(response.content)

            if os.path.getsize(temp_path) < 1000:
                return None

            y, sr = AudioAnalysisService.decode_with_av(temp_path)
            if y is None or len(y) == 0:
                return None

            # Feature Extraction
            tempo_result, _ = librosa.beat.beat_track(y=y, sr=sr)
            tempo = float(tempo_result[0]) if hasattr(tempo_result, "__len__") else float(tempo_result)

            rms = librosa.feature.rms(y=y)
            energy = min(1.0, float(np.mean(rms)) * 2.5)

            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr)
            danceability = min(1.0, float(np.mean(pulse)) * 2.0)

            centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            norm_centroid = np.mean(centroid) / (sr / 2)
            valence = min(1.0, max(0.0, float((norm_centroid * 0.7) + (min(tempo, 180) / 180 * 0.3))))

            y_harmonic, y_percussive = librosa.effects.hpss(y)
            harm_ratio = float(np.sum(np.abs(y_harmonic)) / (np.sum(np.abs(y)) + 1e-6))
            acousticness = harm_ratio * (1.0 - energy * 0.5)
            if tempo > 130: acousticness *= 0.6
            acousticness = min(1.0, max(0.0, acousticness))

            flatness = librosa.feature.spectral_flatness(y=y)
            instrumentalness = 1.0 - float(np.mean(flatness))
            if energy > 0.6: instrumentalness = min(1.0, instrumentalness * 1.2)
            instrumentalness = min(1.0, max(0.0, instrumentalness - 0.4))

            zcr = librosa.feature.zero_crossing_rate(y)
            speechiness = min(1.0, float(np.mean(zcr)) * 5.0)

            loudness = float(librosa.amplitude_to_db([np.mean(rms)], ref=1.0)[0])

            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            mean_chroma = np.mean(chroma, axis=1)
            key = int(np.argmax(mean_chroma))
            major_profile = [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]
            shifted_profile = np.roll(major_profile, key)
            correlation = np.corrcoef(mean_chroma, shifted_profile)[0, 1]
            mode = 1 if correlation > 0 else 0

            return {
                "tempo": round(tempo, 1),
                "energy": round(energy, 3),
                "danceability": round(danceability, 3),
                "valence": round(valence, 3),
                "acousticness": round(acousticness, 3),
                "instrumentalness": round(instrumentalness, 3),
                "speechiness": round(speechiness, 3),
                "loudness": round(loudness, 1),
                "key": key,
                "mode": mode
            }

        except Exception as e:
            traceback.print_exc()
            return None
        finally:
            if temp_path and os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass
