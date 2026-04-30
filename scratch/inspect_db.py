
from app import create_app, db
from sqlalchemy import inspect
import os

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Total tablas en BD: {len(tables)}")
    print("-" * 50)
    for table_name in tables:
        columns = inspector.get_columns(table_name)
        col_names = [c['name'] for c in columns]
        print(f"Table: {table_name}")
        print(f"Columns: {', '.join(col_names)}")
        print("-" * 20)
