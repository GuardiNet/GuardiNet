from flask import Flask, request
from flask_wtf.csrf import CSRFProtect, request
from flask_wtf.csrf import CSRFProtect
from app.config import Config
from app.models import db, bcrypt, User
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per day", "100 per hour"], storage_uri="memory://")

from flask_mail import Mail

mail = Mail()


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # Security setup: CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Security setup: HTTP Security Headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Basic CSP that allows scripts and styles from same origin and trusted CDNs
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net https://code.jquery.com https://unpkg.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'"
        )
        response.headers['Content-Security-Policy'] = csp
        return response


    login_manager = LoginManager()
    login_manager.login_view = 'main.login'  # Define your login route
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.filter_by(user_id=user_id).first()

    # Register blueprints
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    return app
