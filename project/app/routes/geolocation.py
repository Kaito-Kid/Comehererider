"""
Geolocation and platform detection routes.
"""
from flask import Blueprint, jsonify
from flask_login import login_required
from app.utils.geolocation import get_client_location, get_platform

geo_bp = Blueprint('geo', __name__, url_prefix='/geo')


@geo_bp.route('/ip')
@login_required
def ip_location():
    """Return approximate location based on client IP."""
    location = get_client_location() or {}
    return jsonify(location)


@geo_bp.route('/platform')
@login_required
def platform():
    """Return detected platform for the client device."""
    return jsonify({'platform': get_platform()})
