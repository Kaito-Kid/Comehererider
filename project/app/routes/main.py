"""
Main routes for ComeHere Rider (CHR).
Handles landing page and general public pages.
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.models import Rider, Consumer, Order, OrderItem
from app import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Landing page with hero section and analytics.
    Per plan.md: Shows count of riders, users, orders completed.
    Redirects logged-in users to their dashboard.
    """
    # Redirect logged-in users to their dashboard
    if current_user.is_authenticated:
        if current_user.role_type == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role_type == 'manager':
            return redirect(url_for('manager.dashboard'))
        elif current_user.role_type == 'rider':
            return redirect(url_for('rider.dashboard'))
        elif current_user.role_type == 'consumer':
            return redirect(url_for('user.dashboard'))
    
    # Get analytics data
    total_riders = db.session.query(Rider).count()
    total_users = db.session.query(Consumer).count()
    total_orders = db.session.query(Order).filter_by(status='completed').count()
    
    # Calculate total items delivered from completed orders
    total_items_delivered = db.session.query(db.func.sum(OrderItem.quantity)).\
        join(Order).filter(Order.status == 'completed').scalar() or 0
    
    return render_template('general/landing.html',
                         total_riders=total_riders,
                         total_users=total_users,
                         total_orders=total_orders,
                         total_items_delivered=total_items_delivered)


@main_bp.route('/terms')
def terms():
    """Terms and conditions page."""
    return render_template('general/terms.html')


@main_bp.route('/privacy')
def privacy():
    """Privacy policy page."""
    return render_template('general/privacy.html')


@main_bp.route('/about')
def about():
    """About page with information about the service."""
    return render_template('general/about.html')


@main_bp.route('/become-rider')
def become_rider():
    """Rider onboarding page with contact instructions."""
    return render_template('general/rider_onboarding.html')
