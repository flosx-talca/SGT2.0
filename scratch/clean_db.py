
from app import create_app, db
from sqlalchemy import inspect, text

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print(f"Encontradas {len(tables)} tablas. Iniciando limpieza...")
    
    # Desactivar temporalmente las foreign keys si es necesario, 
    # pero CASCADE en TRUNCATE es más limpio en Postgres.
    for table_name in tables:
        if table_name == 'alembic_version':
            print(f"Saltando {table_name} (versión de migraciones)")
            continue
            
        print(f"Limpiando tabla: {table_name}...")
        try:
            # PostgreSQL syntax for truncating with cascade
            db.session.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
        except Exception as e:
            print(f"Error limpiando {table_name}: {e}")
    
    db.session.commit()
    print("--- Limpieza completada ---")
