# Registro de Problemas y Limitaciones Técnicas

Este documento detalla los desafíos técnicos, limitaciones de APIs externas y errores conocidos encontrados durante el desarrollo del proyecto.

## 1. Limitaciones de la API de Spotify (Restricción de Audio Features)

- **Fecha de detección:** 14 de marzo de 2026 (Referencia a cambios globales de Spotify en enero 2025).
- **Problema:** El endpoint `https://api.spotify.com/v1/audio-features/` devuelve un error **403 Forbidden** para muchas aplicaciones, impidiendo obtener datos técnicos como `danceability`, `energy`, `valence`, etc.
- **Causa:** Spotify ha restringido el acceso a estas métricas técnicas a aplicaciones que no hayan pasado una revisión específica o que no cumplan con nuevos criterios de uso.
- **Impacto:** El sistema de recomendación local basado en similitud de coseno (Cosine Similarity) recibe valores en 0 para estas características, lo que lo hace ineficaz.
- **Solución implementada (Fallback):** 
    - Se ha modificado el backend para manejar el error 403 sin interrumpir la ejecución.
    - Se implementó un sistema de "respaldo" que detecta la falta de datos técnicos y consulta el endpoint oficial de recomendaciones de Spotify (`/v1/recommendations`) usando como semilla los IDs de las últimas canciones escuchadas.

## 2. Compatibilidad de Datos (Legacy Data)

- **Problema:** Los datasets generados por versiones anteriores del script (`data_user.csv`) carecían de columnas esenciales para el nuevo esquema de la API.
- **Impacto:** Al intentar leer el CSV antiguo con el nuevo servicio, se producían errores de tipo `KeyError`.
- **Solución implementada:** Se añadió una capa de validación en `data_service.py` que comprueba la existencia de las columnas mínimas requeridas. Si no se encuentran, los datos antiguos se ignoran para forzar una nueva sincronización limpia y evitar fallos del servidor.

## 3. Entorno de Ejecución (Windows/Python 3.14)

- **Problema:** Errores de permisos al intentar instalar dependencias de forma global con `pip` en ciertos entornos de Windows.
- **Solución recomendada:** Uso de entornos virtuales (`.venv`) y ejecución de scripts mediante el wrapper de Python `py` o `python` dependiendo de la configuración del usuario. 

## 4. Estructura de Proyecto (Refactorización)

- **Problema:** Desorden inicial en la raíz del proyecto con múltiples scripts duplicados (`main.py`, `getData.py`).
- **Solución:** Consolidación total bajo la carpeta `backend/` siguiendo los estándares de `PROJECT_ARCHITECTURE.md`.

---
*Este documento debe ser actualizado cada vez que se detecte una limitación persistente o una decisión de diseño crítica motivada por factores externos.*
