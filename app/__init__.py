import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
from config import Config, DevelopmentConfig, ProductionConfig

# Load environment variables from .env
load_dotenv()

# Initialize extensions **without app**
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = "info"  # optional, for flash messages

def create_app():
    app = Flask(__name__)

    # Pick config based on FLASK_ENV
    config_type = os.getenv("FLASK_ENV", "development").lower()
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "default": Config
    }
    app.config.from_object(config_map.get(config_type, DevelopmentConfig))

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Import and register blueprints **after db init**
    from .routes import main
    from .routes.auth import auth_bp

    app.register_blueprint(main)
    app.register_blueprint(auth_bp)

    # Ensure SQLite database exists (for both dev and prod)
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        with app.app_context():
            db.create_all()

    return app
