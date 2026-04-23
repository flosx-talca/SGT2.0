import os
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
print(f"Probando SQLAlchemy con: {db_url}")

try:
    # Quitamos el parámetro de encoding si existe para ver si SQLAlchemy lo maneja solo
    clean_url = db_url.split('?')[0] if '?' in db_url else db_url
    print(f"Usando URL limpia: {clean_url}")
    
    engine = create_engine(clean_url)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        print(f"✅ ¡SQLAlchemy conectó! {result.fetchone()}")
except Exception as e:
    print("❌ Error en SQLAlchemy:")
    print(f"Tipo: {type(e)}")
    try:
        print(f"Error: {e}")
    except UnicodeDecodeError:
        print("Error de decodificación al imprimir el error.")
    print(f"Representación técnica: {repr(e)}")
