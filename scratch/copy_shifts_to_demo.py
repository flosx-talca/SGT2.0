
from app import create_app, db
from app.models.business import Empresa, Turno, TurnoPlantilla

def copy_shifts():
    app = create_app()
    with app.app_context():
        print("--- Copiando Plantillas de Turnos a Empresas Demo ---")
        
        # Obtener plantillas globales
        plantillas = TurnoPlantilla.query.all()
        if not plantillas:
            print("Error: No hay plantillas de turnos globales.")
            return

        # Obtener las 3 empresas más recientes
        empresas = Empresa.query.order_by(Empresa.id.desc()).limit(3).all()
        
        for e in empresas:
            print(f"Procesando Empresa: {e.razon_social}")
            for p in plantillas:
                # Verificar si ya tiene un turno con la misma abreviación
                existente = Turno.query.filter_by(empresa_id=e.id, abreviacion=p.abreviacion).first()
                if not existente:
                    nuevo_turno = Turno(
                        empresa_id=e.id,
                        nombre=p.nombre,
                        abreviacion=p.abreviacion,
                        hora_inicio=p.hora_inicio,
                        hora_fin=p.hora_fin,
                        color=p.color,
                        dotacion_diaria=p.dotacion_diaria,
                        es_nocturno=p.es_nocturno,
                        es_base=True
                    )
                    db.session.add(nuevo_turno)
                    print(f" -> Creado turno: {p.nombre} ({p.abreviacion})")
                else:
                    print(f" -> Turno {p.abreviacion} ya existe.")

        db.session.commit()
        print("--- Proceso Finalizado ---")

if __name__ == "__main__":
    copy_shifts()
