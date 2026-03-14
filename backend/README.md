# Spotify Wrapped Rework - Backend

Este es el backend de la aplicación Spotify Wrapped Rework, diseñado para analizar tu historial de música y generar recomendaciones personalizadas utilizando un motor de análisis de audio propio.

## 🚀 Cómo funciona el proyecto (Estado Actual)

Debido a las recientes restricciones de la API de Spotify (2024-2025), el proyecto ha evolucionado de ser un simple cliente de API a un sistema de procesamiento de audio autónomo.

### 1. Sincronización de Datos
El sistema recupera tus canciones más escuchadas y reproducidas recientemente de Spotify. Si la API de Spotify bloquea el acceso a las "Audio Features" (Error 403), el sistema activa automáticamente su **motor de análisis local**.

### 2. Motor de Análisis de Audio (DSP)
Utilizamos procesamiento digital de señales para extraer métricas musicales directamente del audio:
- **Bibliotecas:** `librosa` para análisis musical y `av` (PyAV) para decodificación de audio universal.
- **Métricas:** Calculamos Tempo (BPM), Energía, Danceability, Valence, Acousticness, Instrumentalness, Speechiness, Key y Mode.

### 3. Sistema de Fallback de Previews
Para analizar el audio, necesitamos un fragmento de la canción. Si Spotify no proporciona el `preview_url`:
1. El sistema consulta la **API de iTunes** automáticamente.
2. Descarga el fragmento de 30 segundos y lo procesa en memoria.

### 4. Curación Incremental
Cada vez que realizas una sincronización (`/sync`), el servidor identifica canciones en tu base de datos local que tienen valores en cero y las "cura" analizando su audio en segundo plano.

## 🛠️ Instalación y Uso

1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Configura tu archivo `.env` con las credenciales de Spotify.
3. Inicia el servidor:
   ```bash
   python run.py
   ```

## 📡 Endpoints Principales

- `GET /api/sync`: Sincroniza datos de Spotify y enriquece la base de datos local.
- `GET /api/analyze-track?song={nombre}&artist={artista}`: Analiza profundamente cualquier canción.
- `GET /api/recommendations`: Genera recomendaciones basadas en tu gusto musical y análisis de audio.
- `GET /api/analysis`: Muestra estadísticas generales de tu biblioteca.
- `GET /api/user-profile`: Perfil de audio promedio del usuario.
