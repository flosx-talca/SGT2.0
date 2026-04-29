import os
import sys
from datetime import time

# Agregar el directorio raíz al path
sys.path.append(os.getcwd())

from app import create_app
from app.database import db
from app.models.business import TipoAusenciaPlantilla, CategoriaAusencia
from app.models.enums import RestrictionType

app = create_app()
with app.app_context():
    ausencias_p = [
        # Ausencias Físicas
        {'nombre': 'Vacaciones', 'abreviacion': 'VAC', 'color': '#2ecc71', 'categoria': CategoriaAusencia.AUSENCIA},
        {'nombre': 'Licencia Médica', 'abreviacion': 'LIC', 'color': '#e74c3c', 'categoria': CategoriaAusencia.AUSENCIA},
        {'nombre': 'Permiso Administrativo', 'abreviacion': 'PER', 'color': '#9b59b6', 'categoria': CategoriaAusencia.AUSENCIA},
        {'nombre': 'Día Libre Fijo', 'abreviacion': 'LIB', 'color': '#95a5a6', 'categoria': CategoriaAusencia.AUSENCIA},
        
        # Restricciones Lógicas (SGT 2.1)
        {'nombre': 'Turno Fijo', 'abreviacion': 'TFIJ', 'color': '#f1c40f', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.TURNO_FIJO.value},
        {'nombre': 'Turno Preferente', 'abreviacion': 'TPRE', 'color': '#e67e22', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.TURNO_PREFERENTE.value},
        {'nombre': 'Solo este Turno', 'abreviacion': 'SOLO', 'color': '#3498db', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.SOLO_TURNO.value},
        {'nombre': 'Excluir Turno', 'abreviacion': 'EXCL', 'color': '#34495e', 'categoria': CategoriaAusencia.RESTRICCION, 'tipo_restriccion': RestrictionType.EXCLUIR_TURNO.value},
    ]
    
    for ap in ausencias_p:
        obj = TipoAusenciaPlantilla.query.filter_by(abreviacion=ap['abreviacion']).first()
        if not obj:
            print(f"Agregando plantilla: {ap['nombre']}")
            db.session.add(TipoAusenciaPlantilla(**ap))
    
    db.session.commit()
    print("Plantillas sincronizadas.")
