from app import create_app
from app.database import db
from sqlalchemy import text

def migrate_prefs():
    app = create_app()
    with app.app_context():
        sql = """
        INSERT INTO trabajador_restriccion_turno
            (trabajador_id, empresa_id, tipo, naturaleza,
             fecha_inicio, fecha_fin, dias_semana, turno_id, activo, creado_en)
        SELECT
            p.trabajador_id,
            t.empresa_id,
            CASE p.tipo
                WHEN 'fijo'        THEN 'turno_fijo'
                WHEN 'solo_turno'  THEN 'solo_turno'
                WHEN 'preferencia' THEN 'turno_preferente'
                ELSE 'turno_preferente'
            END,
            CASE p.tipo
                WHEN 'preferencia' THEN 'soft'
                ELSE 'hard'
            END,
            CURRENT_DATE,
            '2099-12-31',
            json_build_array(p.dia_semana),
            (SELECT id FROM turno
             WHERE abreviacion = p.turno
             AND empresa_id = t.empresa_id
             LIMIT 1),
            true,
            NOW()
        FROM trabajador_preferencia p
        JOIN trabajador t ON t.id = p.trabajador_id
        WHERE NOT EXISTS (
            SELECT 1 FROM trabajador_restriccion_turno r
            WHERE r.trabajador_id = p.trabajador_id
            AND r.dias_semana::text = json_build_array(p.dia_semana)::text
            AND r.fecha_fin = '2099-12-31'
        );
        """
        try:
            db.session.execute(text(sql))
            db.session.commit()
            
            count_old = db.session.execute(text("SELECT COUNT(*) FROM trabajador_preferencia")).scalar()
            count_new = db.session.execute(text("SELECT COUNT(*) FROM trabajador_restriccion_turno")).scalar()
            
            print(f"Migración de datos exitosa.")
            print(f"Registros en trabajador_preferencia: {count_old}")
            print(f"Registros en trabajador_restriccion_turno: {count_new}")
        except Exception as e:
            db.session.rollback()
            print(f"Error en migración: {e}")

if __name__ == "__main__":
    migrate_prefs()
