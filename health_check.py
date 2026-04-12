import os
import sys

# Add app to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

try:
    from app.main import app
    print("SUCCESS: FastAPI app initialized correctly.")
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
