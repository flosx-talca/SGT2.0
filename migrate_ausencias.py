import sqlite3
from app import create_app
from app.database import db
from app.models.business import TipoAusencia, TrabajadorAusencia, Empresa
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        print("Iniciando migración de TipoAusencia...")
        
        # 1. Crear tabla tipo_ausencia
        db.create_all()
        print("Tabla tipo_ausencia creada si no existía.")
        
        # 2. Agregar columna tipo_ausencia_id a trabajador_ausencia usando raw sql
        # ya que SQLAlchemy no hace ALTER TABLE automático
        try:
            db.session.execute(text("ALTER TABLE trabajador_ausencia ADD COLUMN tipo_ausencia_id INTEGER REFERENCES tipo_ausencia(id) ON DELETE CASCADE"))
            db.session.commit()
            print("Columna tipo_ausencia_id añadida.")
        except Exception as e:
            db.session.rollback()
            if "duplicate column name" in str(e).lower():
                print("La columna tipo_ausencia_id ya existe, omitiendo...")
            else:
                print(f"Nota en ALTER TABLE: {e}")

        # 3. Crear tipos de ausencia por defecto
        empresa = Empresa.query.first()
        if not empresa:
            print("ERROR: No hay empresa. Abortando.")
            return

        tipos_defaults = [
            {'nombre': 'Vacaciones', 'abreviacion': 'V', 'color': '#e74c3c'},
            {'nombre': 'Licencia Médica', 'abreviacion': 'LM', 'color': '#f39c12'},
            {'nombre': 'Permiso', 'abreviacion': 'PER', 'color': '#9b59b6'},
            {'nombre': 'Ausencia General', 'abreviacion': 'A', 'color': '#95a5a6'}
        ]
        
        for td in tipos_defaults:
            ta = TipoAusencia.query.filter_by(abreviacion=td['abreviacion']).first()
            if not ta:
                ta = TipoAusencia(
                    empresa_id=empresa.id,
                    nombre=td['nombre'],
                    abreviacion=td['abreviacion'],
                    color=td['color'],
                    activo=True
                )
                db.session.add(ta)
        db.session.commit()
        print("Tipos de ausencia iniciales insertados.")

        # 4. Migrar registros existentes
        mapa_tipos = {ta.abreviacion: ta for ta in TipoAusencia.query.all()}
        
        ausencias = TrabajadorAusencia.query.all()
        # Nota: SQLAlchemy 2.0 podría quejarse de que TrabajadorAusencia ya no tiene el atributo motivo si
        # lo quitamos del modelo, pero como no actualizamos el esquema de SQLite, `motivo` sigue ahí.
        # Vamos a accederlo vía raw SQL para estar seguros:
        raw_ausencias = db.session.execute(text("SELECT id, motivo FROM trabajador_ausencia")).fetchall()
        
        for row in raw_ausencias:
            a_id = row[0]
            motivo_raw = str(row[1]).strip().upper()
            
            # Buscar coincidencia
            if motivo_raw in ['V', 'VACACION', 'VACACIONES']:
                ta_id = mapa_tipos['V'].id
            elif motivo_raw in ['LM', 'LICENCIA']:
                ta_id = mapa_tipos['LM'].id
            elif motivo_raw == 'PER':
                ta_id = mapa_tipos['PER'].id
            else:
                ta_id = mapa_tipos['A'].id
                
            db.session.execute(
                text("UPDATE trabajador_ausencia SET tipo_ausencia_id = :ta_id WHERE id = :id"),
                {"ta_id": ta_id, "id": a_id}
            )
            
        db.session.commit()
        print("Migración de datos antiguos completada.")

if __name__ == '__main__':
    migrate()
