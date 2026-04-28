import sys, os
sys.path.append(os.getcwd())
from app import create_app
from app.models.business import Trabajador, Turno, Empresa
from app.database import db
from datetime import time

app = create_app()
with app.app_context():
    emp_id = 2 # Empresa de Orlando
    
    # 1. Crear Turnos
    turnos_data = [
        ('Mañana', 'M', time(8, 0), time(16, 0), '#f1c40f', False),
        ('Tarde', 'T', time(16, 0), time(0, 0), '#e67e22', False),
        ('Noche', 'N', time(0, 0), time(8, 0), '#2c3e50', True),
    ]
    
    for nombre, abrev, inicio, fin, color, es_nocturno in turnos_data:
        t = Turno.query.filter_by(empresa_id=emp_id, abreviacion=abrev).first()
        if not t:
            t = Turno(
                empresa_id=emp_id,
                nombre=nombre,
                abreviacion=abrev,
                hora_inicio=inicio,
                hora_fin=fin,
                color=color,
                es_nocturno=es_nocturno,
                activo=True
            )
            db.session.add(t)
    
    # 2. Crear Trabajadores
    trabajadores_data = [
        ('11111111-1', 'Juan', 'Perez', 'j.perez@email.com'),
        ('22222222-2', 'Maria', 'Gonzalez', 'm.gonzalez@email.com'),
        ('33333333-3', 'Carlos', 'Soto', 'c.soto@email.com'),
        ('44444444-4', 'Ana', 'Rojas', 'a.rojas@email.com'),
        ('55555555-5', 'Luis', 'Morales', 'l.morales@email.com'),
    ]
    
    for rut, nombre, apellido, email in trabajadores_data:
        tr = Trabajador.query.filter_by(empresa_id=emp_id, rut=rut).first()
        if not tr:
            tr = Trabajador(
                empresa_id=emp_id,
                servicio_id=1, # Pista Combustible
                rut=rut,
                nombre=nombre,
                apellido1=apellido,
                email=email,
                activo=True
            )
            db.session.add(tr)
            
    db.session.commit()
    print(f"Datos de prueba creados para Empresa ID {emp_id}.")
