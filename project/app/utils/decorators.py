"""
Custom decorators for role-based access control.
Implements decorators per plan.md role specifications.
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user, logout_user


def role_required(*roles):
    """
    Decorator to restrict access to specific roles.
    Usage: @role_required('admin', 'manager')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role_type not in roles:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to restrict access to administrators only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role_type != 'admin':
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def manager_required(f):
    """Decorator to restrict access to managers only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role_type != 'manager':
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def rider_required(f):
    """Decorator to restrict access to riders only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role_type != 'rider':
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def consumer_required(f):
    """Decorator to restrict access to consumers only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role_type != 'consumer':
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def terms_required(f):
    """Decorator to ensure user has accepted terms and privacy policy."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.terms_accepted or not current_user.privacy_accepted:
            flash('You must accept the terms and conditions to continue.', 'warning')
            return redirect(url_for('auth.accept_terms'))
        
        return f(*args, **kwargs)
    return decorated_function


def account_status_required(f):
    """Decorator to check account status and automatically log out suspended/banned users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Check if account is active
        if not current_user.is_account_active():
            # Log out the user
            logout_user()
            
            # Get latest action for detailed message
            from app.models import AccountAction
            latest_action = AccountAction.query.filter_by(user_id=current_user.id)\
                .order_by(AccountAction.created_at.desc()).first()
            
            # Provide appropriate message based on status
            status = current_user.get_account_status()
            status_display = current_user.get_account_status_display()
            
            if status == 'banned':
                reason = latest_action.reason if latest_action else 'No reason provided'
                flash(f'Your account has been {status_display.lower()}. Reason: {reason}', 'error')
            elif status == 'suspended':
                reason = latest_action.reason if latest_action else 'No reason provided'
                if latest_action and latest_action.suspension_until:
                    flash(f'Your account is {status_display.lower()} until {latest_action.suspension_until.strftime("%B %d, %Y at %I:%M %p")}. Reason: {reason}', 'error')
                else:
                    flash(f'Your account is {status_display.lower()}. Reason: {reason}', 'error')
            else:
                flash(f'Your account access has been restricted.', 'error')
            
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function
