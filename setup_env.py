import os

def create_env():
    print("--- Configuración de Entorno SGT 2.0 ---")
    user = input("Usuario Postgres [postgres]: ") or "postgres"
    password = input("Contraseña Postgres: ")
    host = input("Host [localhost]: ") or "localhost"
    port = input("Puerto [5432]: ") or "5432"
    dbname = input("Nombre Base de Datos [sgt]: ") or "sgt"

    db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    with open(".env", "w") as f:
        f.write(f"DATABASE_URL={db_url}\n")
    
    print("\n[OK] Archivo .env creado con éxito.")
    print(f"URL: postgresql://{user}:******@{host}:{port}/{dbname}")

if __name__ == "__main__":
    create_env()
