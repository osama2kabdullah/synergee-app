import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from config import Config, DevelopmentConfig, ProductionConfig

# Load environment variables from .env
load_dotenv()

# Initialize extensions without app
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = "info"

db = SQLAlchemy()

# Import hard-coded user
from .user import HARDCODED_USER

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

    # Ensure persistent directory exists
    os.makedirs("/var/data", exist_ok=True)

    # Use .env database URI if available, else fallback to persistent path
    db_uri = os.getenv("DEV_DATABASE_URI") if config_type == "development" else os.getenv("DATABASE_URI")
    if not db_uri:
        db_uri = "sqlite:////var/data/app.db"

    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    login_manager.init_app(app)
    db.init_app(app)

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        if str(HARDCODED_USER.id) == str(user_id):
            return HARDCODED_USER
        return None

    # Import and register blueprints
    from .routes import main
    from .routes.auth import auth_bp
    app.register_blueprint(main)
    app.register_blueprint(auth_bp)

    # Initialize database tables
    with app.app_context():
        db.create_all()

    return app
