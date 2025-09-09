from app import create_app, db
import json

app = create_app()
with app.app_context():
    # Make sure tables exist
    db.create_all()

    with open("db_export.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for table, rows in data.items():
        for row in rows:
            # Build insert query
            keys = ", ".join(row.keys())
            placeholders = ", ".join([f":{k}" for k in row.keys()])
            query = db.text(f"INSERT INTO {table} ({keys}) VALUES ({placeholders})")
            db.session.execute(query, row)

    db.session.commit()
    print("✅ Data imported successfully!")
