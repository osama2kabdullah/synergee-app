from sqlalchemy import text
from app import create_app, db
import json

app = create_app()
with app.app_context():
    with open("db_export.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for table, rows in data.items():
        for row in rows:
            try:
                # Skip auto-increment identity columns if present
                filtered_row = {k: v for k, v in row.items() if k.lower() != "id"}
                
                keys = ", ".join([f"[{k}]" for k in filtered_row.keys()])
                placeholders = ", ".join([f":{k}" for k in filtered_row.keys()])
                
                query = text(f"INSERT INTO [{table}] ({keys}) VALUES ({placeholders})")
                db.session.execute(query, filtered_row)
            except Exception as e:
                print(f"⚠️ Failed to insert row into {table}: {e}")

    db.session.commit()
    print("✅ Data imported successfully!")
