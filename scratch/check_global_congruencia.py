
from app import create_app, db
from sqlalchemy import inspect
import os

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    db_tables = inspector.get_table_names()
    
    # Obtener todos los modelos registrados en SQLAlchemy
    models = db.Model.registry.mappers
    
    print("AUDITORÍA DE CONGRUENCIA GLOBAL (MODELO vs BD)")
    print("=" * 60)
    
    mismatches = 0
    for mapper in models:
        model_class = mapper.class_
        table_name = model_class.__tablename__
        
        if table_name not in db_tables:
            print(f"[!] Tabla '{table_name}' (Modelo: {model_class.__name__}) NO EXISTE en BD.")
            mismatches += 1
            continue
            
        # Columnas en BD
        db_cols = {c['name']: str(c['type']) for c in inspector.get_columns(table_name)}
        
        # Columnas en Modelo
        model_cols = [c.key for c in mapper.columns]
        
        print(f"Verificando: {table_name} ({model_class.__name__})")
        
        # 1. ¿Falta algo en la BD que esté en el modelo?
        for m_col in model_cols:
            if m_col not in db_cols:
                print(f"   [ERROR] Columna '{m_col}' definida en MODELO pero FALTANTE en BD.")
                mismatches += 1
        
        # 2. ¿Hay algo en la BD que no esté en el modelo?
        for d_col in db_cols:
            if d_col not in model_cols:
                # Omitir ids de tablas de relación si no están mapeados como clases
                print(f"   [AVISO] Columna '{d_col}' existe en BD pero no está mapeada en el MODELO.")
        
        print(f"   [OK] {len(model_cols)} columnas verificadas.")
        print("-" * 40)

    print(f"\nResumen: {mismatches} discrepancias críticas encontradas.")
