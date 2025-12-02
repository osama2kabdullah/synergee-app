from app import create_app, db
from sqlalchemy import text
import json
import datetime, decimal

app = create_app()
with app.app_context():
    data = {}

    for table in db.metadata.tables.keys():
        rows = db.session.execute(text(f"SELECT * FROM {table}")).mappings().all()
        data[table] = [
            {k: (str(v) if isinstance(v, (datetime.datetime, datetime.date, decimal.Decimal)) else v)
             for k, v in row.items()}
            for row in rows
        ]

    with open("db_export.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print("✅ Database exported successfully!")