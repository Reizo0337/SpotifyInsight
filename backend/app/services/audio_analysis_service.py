import requests
import io
import os
import time
import traceback
import av
import numpy as np
import librosa

class AudioAnalysisService:
    @staticmethod
    def get_preview_from_itunes(song, artist):
        """
        Fallback to iTunes API to get a 30s preview URL.
        """
        try:
            # Better search query for iTunes
            query = f"{song} {artist}"
            url = "https://itunes.apple.com/search"
            params = {"term": query, "limit": 3, "media": "music"}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    # Match name as much as possible
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
                    # Use the first result (most relevant)
                    top = results[0]
                    # Simulate popularity from rank (not perfect but better than 0)
                    # We can use the result count or just default to 50 if found
                    return {
                        "genre": top.get("primaryGenreName", "Unknown"),
                        "popularity": 60 + (10 if "contentAdvisoryRating" in top else 0), # Heuristic
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
        
        # Resample to 22050 for consistency with librosa default
        resampler = av.AudioResampler(format='s16', layout='mono', rate=22050)
        
        samples = []
        for frame in container.decode(stream):
            frame.pts = None # Needed for some formats
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
        import time
        t_start = time.time()
        if not preview_url:
            return None

        temp_path = None
        try:
            # Download the preview
            response = requests.get(preview_url, timeout=10)
            if response.status_code != 200:
                print(f"Failed to download preview: {response.status_code}")
                return None

            # Determine extension from URL to avoid decoder confusion
            ext = ".mp3"
            if ".m4a" in preview_url.lower() or "aac" in preview_url.lower():
                ext = ".m4a"
            
            temp_path = f"temp_preview_{int(time.time())}{ext}"
            
            with open(temp_path, "wb") as f:
                f.write(response.content)

            # Check file size
            if os.path.getsize(temp_path) < 1000:
                print("Downloaded file is too small (corrupted?)")
                return None

            # Load audio using PyAV to avoid NoBackendError on Windows
            t_dec = time.time()
            print(f"[ANALYSIS] Decoding {temp_path} using PyAV...")
            y, sr = AudioAnalysisService.decode_with_av(temp_path)
            print(f"[ANALYSIS] Decoding took {time.time()-t_dec:.3f}s")
            
            if y is None or len(y) == 0:
                print("[ANALYSIS] Decoding failed: result is empty")
                return None

            t_feat = time.time()
            print("[ANALYSIS] Extracting features (librosa)...")
            # 1. Tempo
            tempo_result, _ = librosa.beat.beat_track(y=y, sr=sr)
            if hasattr(tempo_result, "__len__"):
                tempo = float(tempo_result[0])
            else:
                tempo = float(tempo_result)

            # 2. Energy (RMS)
            rms = librosa.feature.rms(y=y)
            energy = float(np.mean(rms))
            # Normalizing energy (assuming max reasonable RMS is 0.5)
            energy = min(1.0, energy * 2.5)

            # 3. Danceability
            # Estimate based on beat strength and regularity
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr)
            danceability = float(np.mean(pulse))
            # Makina and fast EDM have high rhythmic regularity. 
            # We scale based on tempo too: faster = usually more "energy" which contributes to dance feel
            danceability = min(1.0, danceability * 2.0)

            # 4. Valence (Happiness/Emotionality)
            # Heuristic: Brightness (Spectral Centroid) + Tempo
            centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            norm_centroid = np.mean(centroid) / (sr / 2)
            valence = float((norm_centroid * 0.7) + (min(tempo, 180) / 180 * 0.3))
            valence = min(1.0, max(0.0, valence))

            # 5. Acousticness
            # Heuristic: High acousticness usually means low energy + high harmonic ratio
            # But electronic music is also harmonic. We add a penalty for high tempo/energy.
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            harm_ratio = float(np.sum(np.abs(y_harmonic)) / (np.sum(np.abs(y)) + 1e-6))
            acousticness = harm_ratio * (1.0 - energy * 0.5)
            # If it's fast, it's less likely to be "acoustic" in the traditional sense
            if tempo > 130:
                acousticness *= 0.6
            acousticness = min(1.0, max(0.0, acousticness))

            # 6. Instrumentalness
            # High spectral flatness = noisy (more likely speech/percussion)
            # Low flatness = tonal (instruments/melodic)
            flatness = librosa.feature.spectral_flatness(y=y)
            avg_flatness = float(np.mean(flatness))
            # Heuristic: if it's high energy and not flat, it's likely instrumental EDM/Makina
            instrumentalness = 1.0 - avg_flatness
            if energy > 0.6:
                instrumentalness = min(1.0, instrumentalness * 1.2)
            instrumentalness = min(1.0, max(0.0, instrumentalness - 0.4))

            # 7. Speechiness
            # Zero crossing rate is higher for speech
            zcr = librosa.feature.zero_crossing_rate(y)
            speechiness = float(np.mean(zcr))
            # Normalizing (speech usually has higher ZCR than music)
            speechiness = min(1.0, speechiness * 5.0)

            # 8. Loudness
            loudness = float(librosa.amplitude_to_db([np.mean(rms)], ref=1.0)[0])
            # Scale to match Spotify (-60 to 0 range usually)
            
            # 9. Key & Mode
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            mean_chroma = np.mean(chroma, axis=1)
            key = int(np.argmax(mean_chroma))
            
            # Simple major/minor heuristic based on chroma
            # Major thirds are usually stronger in major keys
            major_profile = [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0] # Simple C Major profile
            # Shift profile to detected key
            shifted_profile = np.roll(major_profile, key)
            correlation = np.corrcoef(mean_chroma, shifted_profile)[0, 1]
            mode = 1 if correlation > 0 else 0

            t_total = time.time() - t_start
            print(f"[ANALYSIS] Analysis completed in {t_total:.3f}s")
            
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
            print(f"Error analyzing audio: {e}")
            traceback.print_exc()
            return None
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
