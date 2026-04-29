import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.getcwd())

from app import create_app
from app.database import db
from app.models.business import Empresa, TipoAusencia, TipoAusenciaPlantilla

app = create_app()
with app.app_context():
    empresas = Empresa.query.all()
    plantillas = TipoAusenciaPlantilla.query.all()
    
    for emp in empresas:
        for p in plantillas:
            # Buscar si la empresa ya tiene este tipo (por abreviación o por tipo_restriccion)
            existe = TipoAusencia.query.filter_by(
                empresa_id=emp.id,
                abreviacion=p.abreviacion
            ).first()
            
            if not existe:
                print(f"Sincronizando {p.nombre} para empresa {emp.razon_social}")
                db.session.add(TipoAusencia(
                    empresa_id=emp.id,
                    nombre=p.nombre,
                    abreviacion=p.abreviacion,
                    color=p.color,
                    categoria=p.categoria,
                    tipo_restriccion=p.tipo_restriccion,
                    es_base=True,
                    activo=True
                ))
    
    db.session.commit()
    print("Sincronización de empresas completada.")
