import os
import sys
from types import ModuleType

# Añadir el directorio raíz al path para evitar errores de importación
sys.path.append(os.getcwd())

# Mock dotenv para entornos donde no esté instalado
m = ModuleType("dotenv")
m.load_dotenv = lambda *args, **kwargs: None
sys.modules["dotenv"] = m

from app import create_app
from app.database import db
from app.models.business import Empresa
from app.seeds.parametros_legales import seed_parametros_legales
from app.seeds.reglas_base import seed_reglas_base
from app.seeds.tipos_ausencia_base import seed_tipos_ausencia_base

def run_all_seeds():
    """
    Script maestro para inicializar todos los datos necesarios del sistema SGT 2.1.
    """
    app = create_app()
    with app.app_context():
        print("====================================================")
        print("   SGT 2.1 - INICIALIZADOR DE DATOS (SEEDING)       ")
        print("====================================================")
        
        try:
            # 1. Parámetros Legales (Límites de jornada, descansos, etc.)
            print("\n[1/3] Sembrando Parámetros Legales...")
            seed_parametros_legales()
            
            # 2. Reglas Base (Lógica del optimizador y penalizaciones)
            print("\n[2/3] Sembrando Reglas de Negocio (Solver)...")
            seed_reglas_base()
            
            # 3. Tipos de Ausencia y Restricciones (Por Empresa)
            print("\n[3/3] Sembrando Tipos de Ausencia y Restricciones...")
            empresas = Empresa.query.all()
            if not empresas:
                print(" (!) ADVERTENCIA: No hay empresas registradas. No se crearon tipos de ausencia.")
            else:
                for e in empresas:
                    print(f" -> Procesando empresa: {e.razon_social} (ID: {e.id})")
                    seed_tipos_ausencia_base(e.id)
            
            print("\n====================================================")
            print("   ¡PROCESO FINALIZADO EXITOSAMENTE!                ")
            print("====================================================")
            
        except Exception as ex:
            print(f"\n [ERROR CRÍTICO] Ocurrió un fallo durante el seeding: {ex}")
            db.session.rollback()

if __name__ == "__main__":
    run_all_seeds()
