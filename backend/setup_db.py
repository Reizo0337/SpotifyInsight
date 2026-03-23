from sqlalchemy import create_engine, text
from app.db.models import Base
import os

# Database details from USER
USER = "root"
PASSWORD = "reizonr1"
HOST = "localhost"
DB_NAME = "nebulamusic"

# 1. Connect without DB first to create it if it doesn't exist
server_url = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}/"
engine = create_engine(server_url)

with engine.connect() as conn:
    print(f"-> Verificando existencia de la base de datos '{DB_NAME}'...")
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
    conn.commit()

# 2. Connect to the actual DB and create tables
db_url = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DB_NAME}"
engine = create_engine(db_url)

print(f"-> Creando tablas para Nebula Music...")
Base.metadata.create_all(bind=engine)

print("\n🚀 ¡Configuración completada con éxito!")
print(f"DATABASE_URL=mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DB_NAME}")
