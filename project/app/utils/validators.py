"""
Input validation utilities for ComeHere Rider (CHR).
Provides validation functions for forms and user input.
"""
import re
from flask import current_app

def validate_phone_number(phone):
    """
    Validate Philippine phone number.
    Accepts formats: 09123456789, +639123456789, 9123456789
    
    Args:
        phone: Phone number string
    
    Returns:
        Tuple (valid: bool, cleaned_number: str or error: str)
    """
    if not phone:
        return False, 'Phone number is required'
    
    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check for valid Philippine mobile number patterns
    patterns = [
        r'^09\d{9}$',           # 09123456789
        r'^\+639\d{9}$',        # +639123456789
        r'^639\d{9}$',          # 639123456789
        r'^9\d{9}$'             # 9123456789
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            # Normalize to 09xxxxxxxxx format
            if cleaned.startswith('+63'):
                cleaned = '0' + cleaned[3:]
            elif cleaned.startswith('63'):
                cleaned = '0' + cleaned[2:]
            elif cleaned.startswith('9'):
                cleaned = '0' + cleaned
            
            return True, cleaned
    
    return False, 'Invalid phone number format. Use: 09123456789'


def validate_email(email):
    """
    Validate email address format.
    
    Args:
        email: Email string
    
    Returns:
        Tuple (valid: bool, error: str or None)
    """
    if not email:
        return False, 'Email is required'
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(pattern, email):
        return True, None
    
    return False, 'Invalid email format'


def validate_password(password):
    """
    Validate password strength.
    Requirements: At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    
    Args:
        password: Password string
    
    Returns:
        Tuple (valid: bool, error: str or None)
    """
    if not password:
        return False, 'Password is required'
    
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one number'
    
    return True, None


def validate_plate_number(plate_number):
    """
    Validate Philippine vehicle plate number.
    
    Args:
        plate_number: Plate number string
    
    Returns:
        Tuple (valid: bool, error: str or None)
    """
    if not plate_number:
        return False, 'Plate number is required'
    
    # Remove spaces and convert to uppercase
    cleaned = re.sub(r'\s', '', plate_number.upper())
    
    # Common Philippine plate formats
    # ABC 1234, ABC-1234, 1234-ABC, etc.
    patterns = [
        r'^[A-Z]{3}\d{3,4}$',      # ABC123, ABC1234
        r'^\d{3,4}[A-Z]{3}$',      # 123ABC, 1234ABC
        r'^[A-Z]{2}\d{4,5}$',      # AB1234, AB12345
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True, None
    
    return False, 'Invalid plate number format'


def validate_address(address):
    """
    Validate address field.
    
    Args:
        address: Address string
    
    Returns:
        Tuple (valid: bool, error: str or None)
    """
    if not address:
        return False, 'Address is required'
    
    if len(address) < 10:
        return False, 'Address must be at least 10 characters'
    
    if len(address) > 500:
        return False, 'Address is too long (max 500 characters)'
    
    return True, None


def sanitize_input(text, max_length=None):
    """
    Sanitize user input by removing potentially dangerous characters.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not text:
        return ''
    
    # Convert to string and strip
    text = str(text).strip()
    
    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_money_amount(amount):
    """
    Validate monetary amount.
    
    Args:
        amount: Amount as string or number
    
    Returns:
        Tuple (valid: bool, float_amount or error: str)
    """
    try:
        amount_float = float(amount)
        
        if amount_float < 0:
            return False, 'Amount cannot be negative'
        
        if amount_float > 100000:
            return False, 'Amount too large (max ₱100,000)'
        
        # Round to 2 decimal places
        amount_float = round(amount_float, 2)
        
        return True, amount_float
    except (ValueError, TypeError):
        return False, 'Invalid amount format'
