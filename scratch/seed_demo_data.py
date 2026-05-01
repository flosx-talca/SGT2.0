
import random
from app import create_app, db
from app.models.business import Cliente, Empresa, Servicio, Trabajador
from app.models.core import Comuna
from app.models.enums import TipoContrato

def generate_rut():
    number = random.randint(10000000, 25000000)
    return f"{number}-{random.choice('0123456789K')}"

def seed_demo_data():
    app = create_app()
    with app.app_context():
        print("--- Iniciando Carga de Datos Demo ---")
        
        # 1. Obtener Comuna y Servicio base
        comuna = Comuna.query.filter_by(codigo='13101').first() # Santiago
        if not comuna:
            print("Error: No se encontró la comuna base.")
            return
            
        servicios = Servicio.query.all()
        if not servicios:
            # Crear servicios si no existen (aunque init_db_full debería haberlos creado)
            servicios = [
                Servicio(descripcion='Pista Combustible'),
                Servicio(descripcion='Tienda Pronto'),
                Servicio(descripcion='Administración')
            ]
            for s in servicios:
                db.session.add(s)
            db.session.flush()
        
        # 2. Configuración de carga
        data_config = [
            {"client_name": "Retail Corp", "emp_name": "Retail - Sucursal Norte", "worker_count": 7},
            {"client_name": "Inversiones ABC", "emp_name": "ABC - Centro Logístico", "worker_count": 14},
            {"client_name": "Logística Global", "emp_name": "Global - Bodega Central", "worker_count": 20}
        ]
        
        nombres = ["Juan", "María", "Pedro", "Ana", "Luis", "Elena", "Carlos", "Sofía", "Diego", "Lucía", "Roberto", "Valentina", "Andrés", "Camila", "Miguel", "Isabella", "Javier", "Florencia", "Ricardo", "Martina"]
        apellidos = ["García", "Rodríguez", "López", "González", "Pérez", "Martínez", "Sánchez", "Álvarez", "Torres", "Ramírez", "Soto", "Contreras", "Sepúlveda", "Morales", "Muñoz", "Rojas", "Díaz", "Silva", "Valenzuela", "Araya"]

        for config in data_config:
            # Crear Cliente
            cliente = Cliente(
                rut=generate_rut(),
                nombre=config["client_name"],
                apellidos="S.A.",
                email=f"contacto@{config['client_name'].lower().replace(' ', '')}.cl"
            )
            db.session.add(cliente)
            db.session.flush()
            
            # Crear Empresa
            empresa = Empresa(
                rut=generate_rut(),
                razon_social=config["emp_name"],
                cliente_id=cliente.id,
                comuna_id=comuna.id,
                direccion=f"Calle Falsa {random.randint(100, 999)}"
            )
            empresa.servicios = [random.choice(servicios)]
            db.session.add(empresa)
            db.session.flush()
            
            # Crear Trabajadores
            num_workers = config["worker_count"]
            num_full_time = int(num_workers * 0.8)
            
            for i in range(num_workers):
                is_full_time = (i < num_full_time)
                
                trabajador = Trabajador(
                    rut=generate_rut(),
                    nombre=random.choice(nombres),
                    apellido1=random.choice(apellidos),
                    apellido2=random.choice(apellidos),
                    empresa_id=empresa.id,
                    servicio_id=empresa.servicios[0].id,
                    cargo="Operador",
                    email=f"worker{i}_{empresa.id}@example.com",
                    tipo_contrato=TipoContrato.FULL_TIME if is_full_time else TipoContrato.PART_TIME_30,
                    horas_semanales=42 if is_full_time else 30
                )
                db.session.add(trabajador)
            
            print(f"Creada Empresa '{config['emp_name']}' con {num_workers} trabajadores.")

        db.session.commit()
        print("--- Carga Demo Completada Exitosamente ---")

if __name__ == "__main__":
    seed_demo_data()
