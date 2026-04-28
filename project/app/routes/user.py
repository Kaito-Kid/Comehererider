"""
User/Consumer routes for ComeHere Rider (CHR).
Handles consumer dashboard and order management functions.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.decorators import consumer_required, account_status_required
from app import db
from app.models import Consumer, Order

user_bp = Blueprint('user', __name__, url_prefix='/user')


@user_bp.route('/dashboard')
@login_required
@consumer_required
@account_status_required
def dashboard():
    """Consumer dashboard with order overview."""
    consumer = current_user
    
    # Get consumer statistics
    active_orders = consumer.orders.filter(Order.status.in_(['pending', 'accepted', 'in_progress'])).count()
    completed_orders = consumer.orders.filter_by(status='completed').count()
    total_orders = consumer.total_orders_placed
    favorite_riders_count = len(consumer.favorite_riders)
    
    return render_template('user/dashboard.html',
                         active_orders=active_orders,
                         completed_orders=completed_orders,
                         total_orders=total_orders,
                         favorite_riders_count=favorite_riders_count)


@user_bp.route('/profile')
@login_required
@consumer_required
@account_status_required
def profile():
    """View consumer profile."""
    return render_template('user/profile.html')


@user_bp.route('/settings')
@login_required
@consumer_required
@account_status_required
def settings():
    """Consumer settings page."""
    return render_template('user/settings.html')
