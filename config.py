import os
from datetime import timedelta


def _parse_origins(raw_value):
    if not raw_value:
        return ['http://localhost:3000', 'http://127.0.0.1:3000']
    return [origin.strip() for origin in raw_value.split(',') if origin.strip()]

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///vollite.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB max file size
    ALLOWED_EXTENSIONS = {'dmp', 'mem', 'raw', 'vmem'}

    # Security configuration
    BCRYPT_LOG_ROUNDS = 12
    APP_ENV = os.environ.get('FLASK_ENV', 'development').lower()

    # Auth rate limiting
    AUTH_REGISTER_RATE_LIMIT = os.environ.get('AUTH_REGISTER_RATE_LIMIT', '30 per minute')
    AUTH_LOGIN_RATE_LIMIT = os.environ.get('AUTH_LOGIN_RATE_LIMIT', '30 per minute')
    AUTH_CHANGE_PASSWORD_RATE_LIMIT = os.environ.get('AUTH_CHANGE_PASSWORD_RATE_LIMIT', '20 per minute')
    AUTH_VERIFY_TOKEN_RATE_LIMIT = os.environ.get('AUTH_VERIFY_TOKEN_RATE_LIMIT', '120 per minute')

    # Flask-Limiter backend
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

    # Volatility configuration
    VOLATILITY_PATH = os.environ.get('VOLATILITY_PATH') or '/usr/local/bin/vol.py'

    # CORS configuration
    CORS_ORIGINS = _parse_origins(os.environ.get('CORS_ORIGINS'))

    # Logging / monitoring configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 1048576))
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 3))

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///vollite_dev.db'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}