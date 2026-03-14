# Spotify Data Analyzer

Aplicación de análisis de datos musicales y recomendación basada en datos de Spotify.

El proyecto analiza datasets de canciones de Spotify, genera métricas sobre los gustos musicales del usuario y recomienda nuevas canciones basadas en similitud musical.

## Funcionalidades

- Análisis de dataset de Spotify
- Visualización de KPI musicales
- Perfil musical del usuario
- Recomendación de canciones similares
- Integración con Spotify API (Spotipy)
- Reproducción de música mediante YouTube
- Interfaz estilo Spotify

## Arquitectura

El proyecto sigue una arquitectura cliente-servidor:

**Backend (Python + FastAPI):**
- Operaciones en `backend/`
- Lógica de negocio en `app/services/`
- API REST en `app/api/`

**Frontend (Vue.js + Electron):**
- Operaciones en `frontend/` (Pendiente de implementación)

## Instalación y Uso

### Backend
1. Ir a la carpeta backend: `cd backend`
2. Instalar dependencias: `pip install -r requirements.txt`
3. Ejecutar: `python run.py`

### Endpoints Principales
- `/api/sync`: Sincroniza datos de Spotify.
- `/api/analysis`: Obtiene métricas del usuario.
- `/api/recommendations`: Sugiere canciones.

## Estructura del proyecto

- `backend/` → Servidor API y lógica.
- `data/` → Datasets (`processed/` contiene el dataset limpio).
- `agent/` → Documentación y reglas del asistente.
- `scripts/` → Utilidades de procesamiento.
