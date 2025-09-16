from app import create_app, db

app = create_app()

with app.app_context():
    db.drop_all()
    print("🗑️  Database and all tables deleted successfully.")
