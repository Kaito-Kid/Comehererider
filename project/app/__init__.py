"""
Flask application factory for ComeHere Rider (CHR).
Initializes Flask app with all extensions and configurations.
"""
import os
import os
import time
import logging
from datetime import datetime
import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import inspect

from app.config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute", "50 per minute"]
)


def create_app(config_name=None):
    """
    Application factory function.
    
    Args:
        config_name: Configuration environment ('development', 'production', 'testing')
    
    Returns:
        Configured Flask application instance
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    CORS(app)
    limiter.init_app(app)
    
    # Configure Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Setup logging
    setup_logging(app)
    
    # Perform startup checks
    with app.app_context():
        startup_checks(app)
        
        # Register blueprints within app context
        register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register security headers
    register_security_headers(app)
    
    # Register custom template filters
    from datetime import timedelta
    
    @app.template_filter('local_time')
    def local_time_filter(dt, format='%Y-%m-%d %I:%M %p'):
        """Convert UTC datetime to PHT (UTC+8) and format."""
        if dt is None:
            return ""
        # Add 8 hours for Philippine Time
        local_dt = dt + timedelta(hours=8)
        return local_dt.strftime(format)
        
    return app


def setup_logging(app):
    """
    Configure application logging.
    Logs are written to both file and console with severity levels.
    """
    if not os.path.exists(app.config['LOG_DIR']):
        os.makedirs(app.config['LOG_DIR'])
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # File handler for all logs (info and above)
    date_str = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(app.config['LOG_DIR'], f'app_{date_str}.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    
    # Separate file handler for errors (high severity)
    error_log_file = os.path.join(app.config['LOG_DIR'], f'errors_{date_str}.log')
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)
    
    # Configure app logger
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)
    
    # Security logger (moderate severity, separate file)
    security_log_file = os.path.join(app.config['LOG_DIR'], f'security_{date_str}.log')
    security_handler = logging.FileHandler(security_log_file)
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(detailed_formatter)
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    security_logger.addHandler(security_handler)
    
    # Attach to app for optional use
    app.security_logger = security_logger
    
    app.logger.info('ComeHere Rider application startup')


def register_security_headers(app):
    """
    Attach common security headers and a CSP suitable for our current CDNs.
    """
    @app.after_request
    def add_security_headers(response):
        # Frame busting
        response.headers['X-Frame-Options'] = 'DENY'
        # MIME sniffing protection
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Referrer policy
        response.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'
        # Content Security Policy (allow required CDNs and OSM tiles)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "img-src 'self' data: blob: https://*; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self' https://tile.openstreetmap.org https://{s}.tile.openstreetmap.org; "
            "frame-ancestors 'none'; "
            "worker-src 'self'; "
            "manifest-src 'self'"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # HSTS in production
        if not app.debug and not app.testing:
            response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
        return response


def print_config_values(app):
    """
    Print application configuration values on startup.
    Masks sensitive information for security.
    """
    print("\n" + "="*60)
    print("COMEHERE RIDER - APPLICATION CONFIGURATION")
    print("="*60)
    
    # Application settings
    print(f"APP_NAME: {app.config.get('APP_NAME', 'N/A')}")
    print(f"SECRET_KEY: {'*' * len(app.config.get('SECRET_KEY', '')) if app.config.get('SECRET_KEY') else 'Not set'}")
    print(f"DEBUG: {app.config.get('DEBUG', 'N/A')}")
    print(f"TESTING: {app.config.get('TESTING', 'N/A')}")
    
    # Database
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')
    # Mask password in database URI
    if 'mysql+pymysql://' in db_uri:
        import re
        db_uri = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', db_uri)
    print(f"DATABASE_URI: {db_uri}")
    print(f"SQLALCHEMY_TRACK_MODIFICATIONS: {app.config.get('SQLALCHEMY_TRACK_MODIFICATIONS', 'N/A')}")
    print(f"SQLALCHEMY_ECHO: {app.config.get('SQLALCHEMY_ECHO', 'N/A')}")
    
    # Upload settings
    print(f"MAX_CONTENT_LENGTH: {app.config.get('MAX_CONTENT_LENGTH', 'N/A')} bytes")
    print(f"UPLOAD_FOLDER: {app.config.get('UPLOAD_FOLDER', 'N/A')}")
    print(f"ALLOWED_IMAGE_EXTENSIONS: {app.config.get('ALLOWED_IMAGE_EXTENSIONS', 'N/A')}")
    print(f"ALLOWED_DOC_EXTENSIONS: {app.config.get('ALLOWED_DOC_EXTENSIONS', 'N/A')}")
    
    # Security settings
    print(f"SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE', 'N/A')}")
    print(f"SESSION_COOKIE_HTTPONLY: {app.config.get('SESSION_COOKIE_HTTPONLY', 'N/A')}")
    print(f"SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE', 'N/A')}")
    
    # Admin credentials (masked)
    admin_username = app.config.get('ADMIN_USERNAME', 'N/A')
    admin_email = app.config.get('ADMIN_EMAIL', 'N/A')
    admin_password = app.config.get('ADMIN_PASSWORD', '')
    print(f"ADMIN_USERNAME: {admin_username}")
    print(f"ADMIN_EMAIL: {admin_email}")
    print(f"ADMIN_PASSWORD: {'*' * len(admin_password) if admin_password else 'Not set'}")
    
    # Logging settings
    print(f"LOG_DIR: {app.config.get('LOG_DIR', 'N/A')}")
    
    # Rate limiting
    print(f"RATELIMIT_STORAGE_URL: {app.config.get('RATELIMIT_STORAGE_URL', 'N/A')}")
    print(f"RATELIMIT_STRATEGY: {app.config.get('RATELIMIT_STRATEGY', 'N/A')}")
    
    print("="*60 + "\n")


def check_admin_account(app):
    """
    Check if admin account exists and matches environment configuration.
    Create or update admin account as needed.
    """
    from app.models import Admin
    
    # Get admin credentials from config
    admin_email = app.config.get('ADMIN_EMAIL', 'admin@comehere.com')
    admin_username = app.config.get('ADMIN_USERNAME', 'admin')
    admin_password = app.config.get('ADMIN_PASSWORD', 'change-this-password')
    
    try:
        # Try to find existing admin by email
        existing_admin = Admin.query.filter_by(email=admin_email).first()
        
        if existing_admin:
            # Check if credentials match
            needs_update = False
            
            if existing_admin.phone_number != admin_username:
                app.logger.info(f'Updating admin phone number from {existing_admin.phone_number} to {admin_username}')
                existing_admin.phone_number = admin_username
                needs_update = True
            
            if not existing_admin.check_password(admin_password):
                app.logger.info('Updating admin password to match environment configuration')
                existing_admin.set_password(admin_password)
                needs_update = True
            
            if needs_update:
                db.session.commit()
                app.logger.info('✓ Admin account updated successfully')
            else:
                app.logger.info('✓ Admin account exists and matches configuration')
        else:
            # Create new admin account
            app.logger.info('Creating new admin account...')
            
            admin = Admin(
                full_name="System Administrator",
                email=admin_email,
                phone_number=admin_username,
                address="System Administration"
            )
            admin.set_password(admin_password)
            admin.accept_terms()  # Mark terms as accepted
            
            db.session.add(admin)
            db.session.commit()
            
            app.logger.info('✓ Admin account created successfully')
            app.logger.info(f'  Email: {admin.email}')
            app.logger.info(f'  Phone: {admin.phone_number}')
    
    except Exception as e:
        app.logger.error(f'✗ Error managing admin account: {str(e)}')
        db.session.rollback()


def initialize_database(app):
    """
    Check if database tables exist and create them if they don't.
    """
    try:
        inspector = inspect(db.engine)
        # Check for a core table to see if DB is initialized
        if not inspector.has_table('admin'):
            app.logger.info('Database tables not found. Creating...')
            db.create_all()
            app.logger.info('✓ Database tables created successfully')
        else:
            app.logger.info('✓ Database tables already exist')
            
    except Exception as e:
        app.logger.error(f'✗ Error initializing database: {str(e)}')


def wait_for_database(app):
    """
    Wait for database to become available.
    Retries every 15 seconds for 5 minutes.
    """
    retries = 20  # 5 minutes / 15 seconds
    interval = 15
    
    for i in range(retries):
        try:
            db.engine.connect()
            app.logger.info('✓ Database connection successful')
            return True
        except Exception as e:
            remaining = retries - i - 1
            if remaining > 0:
                app.logger.warning(f'Database connection failed. Retrying in {interval} seconds... (Attempt {i+1}/{retries})')
                time.sleep(interval)
            else:
                app.logger.critical(f'Database connection failed after 5 minutes: {str(e)}')
                # Log to a specific error file if needed, but critical logger handles it
                return False
    return False


def startup_checks(app):
    """
    Perform system startup checks for services and dependencies.
    Logs any issues found during startup.
    """
    app.logger.info('Performing startup checks...')
    
    # Print configuration values
    print_config_values(app)
    
    # Initialize database tables
    initialize_database(app)
    
    # Check and create/update admin account
    check_admin_account(app)
    
    # Check database connection with retry
    if not wait_for_database(app):
        # If DB fails, we might want to exit or continue with limited functionality
        # For now, we just log the critical error as requested
        pass
    
    # Check required directories
    required_dirs = [
        app.config['UPLOAD_FOLDER'],
        app.config['LOG_DIR']
    ]
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            app.logger.info(f'✓ Created directory: {directory}')
        else:
            app.logger.info(f'✓ Directory exists: {directory}')
    
    # Check environment variables
    critical_vars = ['SECRET_KEY', 'DATABASE_URI']
    for var in critical_vars:
        if not app.config.get(var.upper().replace('_URI', '_DATABASE_URI') if 'URI' in var else var):
            app.logger.warning(f'⚠ Environment variable {var} not set, using default')
    
    app.logger.info('Startup checks completed')


def register_blueprints(app):
    """Register Flask blueprints for application routes."""
    # Import blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.manager import manager_bp
    from app.routes.rider import rider_bp
    from app.routes.user import user_bp
    from app.routes.orders import orders_bp
    from app.routes.reports import reports_bp
    from app.routes.favorites import favorites_bp
    from app.routes.profile import profile_bp
    from app.routes.geolocation import geo_bp
    from app.routes.api import api_bp
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(rider_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(geo_bp)
    app.register_blueprint(api_bp)
    
    app.logger.info('All blueprints registered successfully')


def register_error_handlers(app):
    """Register error handlers for common HTTP errors."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'404 error: {error}')
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'500 error: {error}')
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f'403 error: {error}')
        return {'error': 'Forbidden'}, 403
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        app.logger.warning(f'401 error: {error}')
        return {'error': 'Unauthorized'}, 401


@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login user loader callback.
    Loads user from database by ID.
    """
    from app.models.user import User
    return User.query.get(int(user_id))
