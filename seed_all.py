import os
import sys
from dotenv import load_dotenv

# Anadir el directorio raiz al path
sys.path.append(os.getcwd())

# Cargar variables de entorno
load_dotenv(override=True)

from app import create_app
from app.database import db
from app.models.business import Empresa
from app.seeds.parametros_legales import seed_parametros_legales
from app.seeds.reglas_base import seed_reglas_base
from app.seeds.tipos_ausencia_base import seed_tipos_ausencia_base
from app.seeds.auth_base import seed_auth_base

def run_all_seeds():
    app = create_app()
    with app.app_context():
        print("====================================================")
        print("   SGT 2.1 - INICIALIZADOR DE DATOS (SEEDING)       ")
        print("====================================================")
        
        try:
            # 0. Autenticacion
            print("\n[0/4] Sembrando Autenticacion...")
            seed_auth_base()

            # 1. Parametros Legales
            print("\n[1/4] Sembrando Parametros Legales...")
            seed_parametros_legales()
            
            # 2. Reglas Base
            print("\n[2/4] Sembrando Reglas de Negocio...")
            seed_reglas_base()
            
            # 3. Tipos de Ausencia
            print("\n[3/4] Sembrando Tipos de Ausencia...")
            empresas = Empresa.query.all()
            for e in empresas:
                print(f" -> Procesando empresa: {e.razon_social}")
                seed_tipos_ausencia_base(e.id)
            
            print("\n====================================================")
            print("   PROCESO FINALIZADO EXITOSAMENTE!                 ")
            print("====================================================")
            
        except Exception as ex:
            import traceback
            print(f"\n [ERROR] Ocurrio un fallo: {ex}")
            traceback.print_exc()
            db.session.rollback()

if __name__ == "__main__":
    run_all_seeds()
