import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
from config import Config, DevelopmentConfig, ProductionConfig

# Load environment variables
load_dotenv()

# Initialize extensions **without app**
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)

    # Pick config
    config_type = os.getenv("FLASK_ENV", "development")
    config_map = {
        "Config": Config,
        "development": DevelopmentConfig,
        "production": ProductionConfig,
    }
    app.config.from_object(config_map.get(config_type, DevelopmentConfig))

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)

    # Import and register blueprints here **after db is ready**
    from .routes import main
    from .routes.auth import auth_bp

    app.register_blueprint(main)
    app.register_blueprint(auth_bp)

    return app
