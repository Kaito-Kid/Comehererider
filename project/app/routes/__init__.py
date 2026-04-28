"""
Routes package for ComeHere Rider (CHR).
Contains all blueprint modules for application routing.
"""
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

__all__ = ['main_bp', 'auth_bp', 'admin_bp', 'manager_bp', 'rider_bp', 'user_bp', 'orders_bp', 'reports_bp', 'favorites_bp', 'profile_bp', 'geo_bp']
