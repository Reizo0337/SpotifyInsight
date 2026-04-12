import uvicorn
import subprocess
import sys
import time
import os

if __name__ == "__main__":
    print("🚀 Iniciando Nebula Music Engine...")
    
    # Lanzar el Samurái (Worker) en un proceso independiente del sistema operativo
    # Esto garantiza que el procesamiento pesado no bloquee la API.
    worker_proc = subprocess.Popen(
        [sys.executable, "-m", "app.worker"],
        stdout=None,
        stderr=None
    )
    
    print("🥷 Samurái Nebula desplegado en segundo plano.")
    
    try:
        # Lanzar la API (FastAPI)
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n🛑 Apagando sistemas...")
    finally:
        # Asegurarnos de que el trabajador también se detenga
        worker_proc.terminate()
        print("🌌 Sistemas Nebula desconectados.")
