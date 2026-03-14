# Registro de Problemas y Soluciones Técnicas

Este documento detalla los obstáculos encontrados durante el desarrollo y cómo han sido superados para mantener la funcionalidad del proyecto.

## 1. Bloqueo de Audio Features de Spotify (Error 403)
- **Problema:** Spotify ha restringido el acceso al endpoint `/audio-features` para muchas aplicaciones, devolviendo `403 Forbidden`. Esto dejaba la base de datos con valores `0,0,0,0`.
- **Solución:** Implementación de un **Motor de Análisis de Audio Local** utilizando la librería `librosa`. Ahora el servidor estima las métricas analizando el sonido directamente.

## 2. Ausencia de Previews en Spotify
- **Problema:** Muchos tracks de Spotify vienen con `preview_url: null`, impidiendo el análisis de audio.
- **Solución:** Se implementó un **Fallback a la API de iTunes**. Si Spotify no da el audio, el servidor busca la canción en iTunes para obtener el fragmento de 30 segundos.

## 3. Error de Decodificación en Windows ("Format not recognised")
- **Problema:** `librosa.load()` fallaba al intentar abrir archivos `.m4a` (formato de iTunes) o `.mp3` en Windows debido a la falta de backends como FFmpeg en el sistema.
- **Solución:** Integración de **PyAV (av)**. Esta librería incluye sus propios decodificadores de FFmpeg vinculados estáticamente, permitiendo al servidor leer cualquier formato de audio de forma nativa e independiente del sistema operativo.

## 4. Problemas de Tipado en Librosa 0.10+
- **Problema:** `librosa.beat.beat_track` devolvía un array en lugar de un escalar, causando errores de tipo al intentar guardar los datos (`TypeError: only 0-dimensional arrays can be converted to Python scalars`).
- **Solución:** Se añadió una capa de validación que detecta si el resultado es una secuencia y extrae el valor principal de forma segura.

## 5. Rendimiento y Bloqueos del Servidor
- **Problema:** El análisis de audio es costoso en CPU y las llamadas paralelas a APIs externas hacían que el servidor de desarrollo se colgara.
- **Solución:**
    - Eliminación de dependencias de APIs lentas (ReccoBeats).
    - Limitación de la curación automática a **5 canciones por sincronización** para evitar picos de carga.
    - Manejo de archivos temporales con limpieza garantizada mediante bloques `finally`.
