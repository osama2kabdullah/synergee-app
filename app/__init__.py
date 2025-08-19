import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from config import Config, DevelopmentConfig, ProductionConfig

# Load environment variables from .env
load_dotenv()

# Initialize extensions **without app**
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = "info"  # optional, for flash messages

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

    # Initialize extensions
    login_manager.init_app(app)

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

    # Removed SQLite/db code since we are using a hard-coded user

    return app
