from app import create_app, db
import json

app = create_app()
with app.app_context():
    data = {}

    # Loop through all tables
    for table in db.metadata.tables.keys():
        rows = db.session.execute(db.text(f"SELECT * FROM {table}")).mappings().all()
        data[table] = [dict(row) for row in rows]

    # Save to file
    with open("db_export.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
