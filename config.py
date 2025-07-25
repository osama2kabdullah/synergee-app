import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    TEMPLATES_AUTO_RELOAD = False

class DevelopmentConfig(Config):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True

class ProductionConfig(Config):
    DEBUG = False
    TEMPLATES_AUTO_RELOAD = False
