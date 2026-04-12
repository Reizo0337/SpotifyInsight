from sqlalchemy import create_engine, text
from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Iniciando migración manual...")
    try:
        conn.execute(text("ALTER TABLE tracks ADD COLUMN view_count INTEGER DEFAULT 0 AFTER popularity"))
        conn.commit()
        print("COLUMNA 'view_count' AÑADIDA CON ÉXITO.")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("LA COLUMNA YA EXISTE.")
        else:
            print(f"ERROR: {e}")
