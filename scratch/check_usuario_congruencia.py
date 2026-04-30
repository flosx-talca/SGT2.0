
from app import create_app, db
from sqlalchemy import inspect
import sys

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    table_name = 'usuario'
    
    if table_name not in inspector.get_table_names():
        print(f"ERROR: La tabla '{table_name}' NO EXISTE en la base de datos.")
        sys.exit(1)
        
    print(f"DETALLE DE CONGRUENCIA: TABLA '{table_name}'")
    print("-" * 50)
    
    # Columnas en BD
    db_columns = {c['name']: str(c['type']) for c in inspector.get_columns(table_name)}
    
    # Columnas esperadas en el Modelo Usuario (auth.py)
    model_expected = [
        'id', 'rut', 'nombre', 'apellidos', 'email', 'password_hash', 
        'rol_id', 'cliente_id', 'empresa_activa_id', 'activo', 
        'creado_en', 'actualizado_en'
    ]
    
    for col in model_expected:
        if col in db_columns:
            print(f"[OK] Campo '{col}': Presente (Tipo BD: {db_columns[col]})")
        else:
            print(f"[ERROR] Campo '{col}': FALTANTE en la base de datos.")
            
    # Verificar si hay columnas extra en BD que no están en el modelo
    extra_cols = [c for c in db_columns if c not in model_expected]
    if extra_cols:
        print("-" * 50)
        print(f"⚠️ Columnas extra en BD (no definidas en el modelo): {extra_cols}")
