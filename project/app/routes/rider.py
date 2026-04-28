"""
Rider routes for ComeHere Rider (CHR).
Handles rider dashboard and delivery management functions.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.decorators import rider_required, account_status_required
from app import db, limiter
from app.models import Rider, Order
from datetime import datetime, timedelta

rider_bp = Blueprint('rider', __name__, url_prefix='/rider')


@rider_bp.route('/dashboard')
@login_required
@rider_required
@account_status_required
def dashboard():
    """Rider dashboard with order and earnings overview."""
    rider = current_user
    
    # Get rider statistics
    pending_orders = rider.orders.filter_by(status='pending').count()
    active_orders = rider.orders.filter(Order.status.in_(['accepted', 'in_progress'])).count()
    completed_orders = rider.total_orders_completed
    total_earnings = rider.total_earnings
    
    return render_template('rider/dashboard.html',
                         pending_orders=pending_orders,
                         active_orders=active_orders,
                         completed_orders=completed_orders,
                         total_earnings=total_earnings,
                         average_rating=rider.average_rating)


@rider_bp.route('/profile')
@login_required
@rider_required
@account_status_required
def profile():
    """View rider profile."""
    return render_template('rider/profile.html')


@rider_bp.route('/settings')
@login_required
@rider_required
@account_status_required
def settings():
    """Rider settings page."""
    return render_template('rider/settings.html')


@rider_bp.route('/payments')
@limiter.limit("50 per minute")
@login_required
@rider_required
@account_status_required
def payments():
    """
    Weekly payments summary for rider.
    Shows completed orders and manager commission owed for a given week.
    Use ?weeks_ago=N to view past weeks (0 = current week).
    """
    try:
        weeks_ago = int(request.args.get('weeks_ago', '0'))
        if weeks_ago < 0:
            weeks_ago = 0
    except ValueError:
        weeks_ago = 0
    
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks_ago)
    end_of_week = start_of_week + timedelta(days=7)  # exclusive
    
    orders = (Order.query
              .filter(Order.rider_id == current_user.id,
                      Order.status == 'completed',
                      Order.completed_at >= datetime.combine(start_of_week, datetime.min.time()),
                      Order.completed_at < datetime.combine(end_of_week, datetime.min.time()))
              .order_by(Order.completed_at.desc())
              .all())
    
    total_orders = len(orders)
    rider_total = sum(o.rider_earnings or 0 for o in orders)
    manager_total = sum(o.manager_earnings or 0 for o in orders)
    
    return render_template('rider/payments.html',
                           orders=orders,
                           total_orders=total_orders,
                           rider_total=rider_total,
                           manager_total=manager_total,
                           start_of_week=start_of_week,
                           end_of_week=end_of_week - timedelta(days=1),
                           weeks_ago=weeks_ago)
