"""
Geolocation utilities for ComeHere Rider (CHR).
Handles IP-based geolocation and coordinate management.
"""
from flask import current_app, request
from functools import lru_cache
import json
from urllib.request import urlopen
from urllib.error import URLError


@lru_cache(maxsize=100)
def get_location_from_ip(ip_address):
    """
    Get location data from IP address using ip-api.com (free service).
    
    Args:
        ip_address: IP address string
    
    Returns:
        Dictionary with location data or None
    """
    # Skip for local/private IPs
    if ip_address in ['127.0.0.1', 'localhost'] or ip_address.startswith('192.168.'):
        return {
            'city': 'Local',
            'region': 'Development',
            'country': 'Philippines',
            'lat': 14.5995,  # Manila coordinates
            'lon': 120.9842,
            'isp': 'Local Network'
        }
    
    try:
        # Use ip-api.com free API (no key required, 45 req/min limit)
        with urlopen(f'http://ip-api.com/json/{ip_address}', timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('status') == 'success':
                    return {
                        'city': data.get('city'),
                        'region': data.get('regionName'),
                        'country': data.get('country'),
                        'lat': data.get('lat'),
                        'lon': data.get('lon'),
                        'isp': data.get('isp'),
                        'zip': data.get('zip'),
                        'timezone': data.get('timezone')
                    }
        current_app.logger.warning(f'Failed to get location for IP: {ip_address}')
        return None
    except URLError as e:
        current_app.logger.error(f'Geolocation API error: {str(e)}')
        return None


def get_client_ip():
    """
    Get client IP address from request, handling proxies.
    
    Returns:
        IP address string
    """
    # Check for proxy headers
    if request.headers.get('X-Forwarded-For'):
        # Get first IP in the list (original client)
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    
    return ip


def get_client_location():
    """
    Get location data for current client.
    
    Returns:
        Dictionary with location data or None
    """
    ip = get_client_ip()
    return get_location_from_ip(ip)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1, lon1: First coordinate (degrees)
        lat2, lon2: Second coordinate (degrees)
    
    Returns:
        Distance in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2
    
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return round(distance, 2)


def validate_coordinates(latitude, longitude):
    """
    Validate coordinate values.
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
    
    Returns:
        Tuple (valid: bool, error: str or None)
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        if not (-90 <= lat <= 90):
            return False, 'Latitude must be between -90 and 90'
        
        if not (-180 <= lon <= 180):
            return False, 'Longitude must be between -180 and 180'
        
        return True, None
        
    except (ValueError, TypeError):
        return False, 'Invalid coordinate format'


def get_platform():
    """
    Detect client platform (Android/iOS/Desktop).
    
    Returns:
        Platform string: 'android', 'ios', or 'desktop'
    """
    user_agent = request.headers.get('User-Agent', '').lower()
    
    if 'android' in user_agent:
        return 'android'
    elif 'iphone' in user_agent or 'ipad' in user_agent:
        return 'ios'
    else:
        return 'desktop'
