import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
if not os.path.exists(INSTANCE_DIR):
    os.makedirs(INSTANCE_DIR, exist_ok=True)


class Config:
    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_for_now_change_in_production'

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')

    # Database configuration
    # For development, use SQLite. For production, configure MySQL in .env
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

    if os.environ.get('DATABASE_URL'):
        # Use custom DATABASE_URL if provided (e.g., MySQL)
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    elif FLASK_ENV == 'production':
        # Production: require MySQL
        db_user = os.environ.get('DB_USER', 'root')
        db_password = os.environ.get('DB_PASSWORD', '')
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_name = os.environ.get('DB_NAME', 'guardinet')

        if db_password:
            SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
        else:
            SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{db_user}@{db_host}/{db_name}'
    else:
        # Development: use SQLite (no external dependency)
        # Use instance folder so the DB is always in a stable location
        instance_db = os.path.join(INSTANCE_DIR, 'guardinet.db')
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{instance_db}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email configuration
    # TO UPDATE: Change these values in .env to real email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'try@gmail.com')  # CHANGE IN .env
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')  # CHANGE IN .env
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@guardinet.local')
