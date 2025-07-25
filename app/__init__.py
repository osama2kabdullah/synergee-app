import os
from flask import Flask
from dotenv import load_dotenv
from config import Config, DevelopmentConfig, ProductionConfig
from .routes import main

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Pick config based on FLASK_CONFIG env var
    config_type = os.getenv("FLASK_ENV")


    config_map = {
        "Config": Config,
        "development": DevelopmentConfig,
        "production": ProductionConfig,
    }

    app.config.from_object(config_map[config_type])

    # Register blueprints
    app.register_blueprint(main)

    return app
