from app import create_app
from app.database import db
from app.models.business import Turno, Trabajador, Servicio, Empresa
from sqlalchemy import text
from datetime import time

app = create_app()
with app.app_context():
    # Obtener una empresa y servicio para asignar los trabajadores
    empresa = Empresa.query.first()
    servicio = Servicio.query.filter_by(activo=True).first()
    
    if not empresa or not servicio:
        print("ERROR: No hay empresa o servicio para asignar.")
        exit(1)
        
    # Desactivar todos los turnos actuales para no chocar
    Turno.query.delete()
    
    # Crear los 4 turnos requeridos
    nuevos_turnos = [
        Turno(empresa_id=empresa.id, nombre='Mañana', abreviacion='M', hora_inicio=time(8,0), hora_fin=time(16,0), activo=True),
        Turno(empresa_id=empresa.id, nombre='Intermedio', abreviacion='I', hora_inicio=time(12,0), hora_fin=time(20,0), activo=True),
        Turno(empresa_id=empresa.id, nombre='Tarde', abreviacion='T', hora_inicio=time(16,0), hora_fin=time(0,0), activo=True),
        Turno(empresa_id=empresa.id, nombre='Noche', abreviacion='N', hora_inicio=time(0,0), hora_fin=time(8,0), activo=True),
    ]
    db.session.add_all(nuevos_turnos)
    
    # Eliminar trabajadores actuales del servicio (opcional, pero pidió borrar)
    Trabajador.query.filter_by(servicio_id=servicio.id).delete()
    
    # Crear 15 trabajadores
    nombres = ['Cesar', 'Leslie', 'Jean', 'Daniel', 'Abraham', 'Sergio', 'Carlos', 'Felipe', 'Mauricio', 'Camila', 'Andrea', 'Miguel', 'Jose', 'Diego', 'Maria']
    apellidos = ['Garcia', 'Waddington', 'Jimenez', 'Parra', 'Manriquez', 'Orellana', 'Medina', 'Astroza', 'Morales', 'Perez', 'Gonzalez', 'Soto', 'Rios', 'Diaz', 'Tapia']
    
    nuevos_trab = []
    for i in range(15):
        rut = f"{10000000+i}-K"
        t = Trabajador(
            rut=rut,
            nombre=nombres[i],
            apellido1=apellidos[i],
            empresa_id=empresa.id,
            servicio_id=servicio.id,
            activo=True
        )
        nuevos_trab.append(t)
        
    db.session.add_all(nuevos_trab)
    db.session.commit()
    print("Base de datos poblada exitosamente con 15 trabajadores y turnos M, I, T, N.")
