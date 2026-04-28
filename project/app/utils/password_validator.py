"""
Password Validation Utilities
CHR - ComeHere Rider Application
"""

import re
import os
from typing import Dict, List, Tuple
from flask import current_app


class PasswordValidator:
    """Server-side password validation utility"""
    
    def __init__(self):
        self.forbidden_passwords = set()
        self.load_forbidden_passwords()
    
    def load_forbidden_passwords(self) -> None:
        """Load forbidden passwords from static file"""
        try:
            forbidden_file = os.path.join(
                current_app.static_folder, 
                'forbidden_passwords.txt'
            )
            
            if os.path.exists(forbidden_file):
                with open(forbidden_file, 'r', encoding='utf-8') as f:
                    passwords = [line.strip().lower() for line in f if line.strip()]
                    self.forbidden_passwords = set(passwords)
            else:
                current_app.logger.warning("Forbidden passwords file not found")
                
        except Exception as e:
            current_app.logger.error(f"Error loading forbidden passwords: {e}")
    
    def validate_password(self, password: str) -> Tuple[bool, Dict[str, bool], List[str]]:
        """
        Validate password against all rules
        
        Returns:
            Tuple of (is_valid, rules_dict, error_messages)
        """
        if not password:
            return False, {}, ["Password is required"]
        
        rules = {
            'length': len(password) >= 8,
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'lowercase': bool(re.search(r'[a-z]', password)),
            'number': bool(re.search(r'[0-9]', password)),
            'special': bool(re.search(r'[@._]', password)),
            'forbidden': password.lower() not in self.forbidden_passwords
        }
        
        error_messages = []
        
        if not rules['length']:
            error_messages.append("Password must be at least 8 characters long")
        
        if not rules['uppercase']:
            error_messages.append("Password must contain at least one uppercase letter (A-Z)")
        
        if not rules['lowercase']:
            error_messages.append("Password must contain at least one lowercase letter (a-z)")
        
        if not rules['number']:
            error_messages.append("Password must contain at least one number (0-9)")
        
        if not rules['special']:
            error_messages.append("Password must contain at least one special character (@._)")
        
        if not rules['forbidden']:
            error_messages.append("Password is too common. Please choose a more secure password")
        
        is_valid = all(rules.values())
        
        return is_valid, rules, error_messages
    
    def get_password_strength(self, password: str) -> Dict[str, any]:
        """
        Calculate password strength score and level
        
        Returns:
            Dict with strength score (0-100) and level (weak/fair/good/strong)
        """
        if not password:
            return {'score': 0, 'level': 'weak'}
        
        is_valid, rules, _ = self.validate_password(password)
        
        # Calculate score based on rules passed
        score = sum(rules.values()) / len(rules) * 100
        
        # Determine strength level
        if score < 33:
            level = 'weak'
        elif score < 66:
            level = 'fair'
        elif score < 100:
            level = 'good'
        else:
            level = 'strong'
        
        return {
            'score': int(score),
            'level': level,
            'is_valid': is_valid,
            'rules': rules
        }
    
    @staticmethod
    def validate_password_match(password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Validate that password and confirmation match
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not confirm_password:
            return False, "Password confirmation is required"
        
        if password != confirm_password:
            return False, "Passwords do not match"
        
        return True, ""


# Global validator instance
password_validator = PasswordValidator()


def validate_password_form(password: str, confirm_password: str = None) -> Dict[str, any]:
    """
    Validate password for form submissions
    
    Args:
        password: The password to validate
        confirm_password: Optional confirmation password
    
    Returns:
        Dict with validation results
    """
    result = {
        'is_valid': False,
        'errors': [],
        'strength': None
    }
    
    # Validate password rules
    is_valid, rules, error_messages = password_validator.validate_password(password)
    result['errors'].extend(error_messages)
    
    # Validate password confirmation if provided
    if confirm_password is not None:
        match_valid, match_error = password_validator.validate_password_match(
            password, confirm_password
        )
        if not match_valid:
            result['errors'].append(match_error)
            is_valid = False
    
    # Get password strength
    result['strength'] = password_validator.get_password_strength(password)
    
    result['is_valid'] = is_valid and (confirm_password is None or match_valid)
    
    return result


def get_password_requirements() -> List[str]:
    """
    Get list of password requirements for display
    
    Returns:
        List of requirement strings
    """
    return [
        "At least 8 characters long",
        "Contains at least one uppercase letter (A-Z)",
        "Contains at least one lowercase letter (a-z)",
        "Contains at least one number (0-9)",
        "Contains at least one special character (@._)",
        "Is not a commonly used password"
    ]
