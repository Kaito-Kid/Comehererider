"""
Manager routes for ComeHere Rider (CHR).
Handles manager dashboard and account management functions.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.utils.decorators import manager_required, account_status_required
from app import db, limiter
from app.models import Manager, Rider, Consumer, Report, Order, User
from datetime import datetime, timedelta

manager_bp = Blueprint('manager', __name__, url_prefix='/manager')


@manager_bp.route('/dashboard')
@login_required
@manager_required
@account_status_required
def dashboard():
    """Manager dashboard with assigned accounts overview."""
    manager = current_user
    is_head = manager.manager_type == 'head'
    
    # Get accounts under management
    if is_head:
        managed_riders_count = Rider.query.count()
        managed_consumers_count = Consumer.query.count()
        pending_reports = Report.query.filter_by(status='pending').count()
    else:
        managed_riders_count = manager.managed_riders.count() if manager.can_manage_riders() else 0
        managed_consumers_count = manager.managed_consumers.count() if manager.can_manage_consumers() else 0
        pending_reports = Report.query.filter_by(handler_id=current_user.id, status='pending').count()
    
    return render_template('manager/dashboard.html',
                         manager_type=manager.manager_type,
                         managed_riders=managed_riders_count,
                         managed_consumers=managed_consumers_count,
                         pending_reports=pending_reports)


@manager_bp.route('/profile')
@login_required
@manager_required
@account_status_required
def profile():
    """View manager profile."""
    return render_template('manager/profile.html')


@manager_bp.route('/settings')
@login_required
@manager_required
@account_status_required
def settings():
    """Manager settings page."""
    return render_template('manager/settings.html')


@manager_bp.route('/payments')
@login_required
@manager_required
@account_status_required
def payments():
    """Weekly payments summary for managed riders."""
    try:
        weeks_ago = int(request.args.get('weeks_ago', '0'))
        if weeks_ago < 0:
            weeks_ago = 0
    except ValueError:
        weeks_ago = 0
    
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks_ago)
    end_of_week = start_of_week + timedelta(days=7)
    
    # Get orders for managed riders (or all if head manager)
    if current_user.manager_type == 'head':
        managed_rider_ids = [r.id for r in Rider.query.all()]
    else:
        managed_rider_ids = [r.id for r in current_user.managed_riders.all()]
    
    if not managed_rider_ids:
        return render_template('manager/payments.html', 
                               orders=[], summary={}, total_orders=0, 
                               rider_total=0, manager_total=0,
                               start_of_week=start_of_week, 
                               end_of_week=end_of_week - timedelta(days=1),
                               weeks_ago=weeks_ago)

    orders = (Order.query
              .filter(Order.rider_id.in_(managed_rider_ids),
                      Order.status == 'completed',
                      Order.completed_at >= datetime.combine(start_of_week, datetime.min.time()),
                      Order.completed_at < datetime.combine(end_of_week, datetime.min.time()))
              .order_by(Order.completed_at.desc())
              .all())
    
    # Group by rider for the summary table
    summary = {}
    for order in orders:
        if order.rider_id not in summary:
            summary[order.rider_id] = {
                'rider': order.rider,
                'orders': 0,
                'rider_total': 0,
                'manager_total': 0
            }
        summary[order.rider_id]['orders'] += 1
        summary[order.rider_id]['rider_total'] += (order.rider_earnings or 0)
        summary[order.rider_id]['manager_total'] += (order.manager_earnings or 0)
    
    total_orders = len(orders)
    rider_total = sum(o.rider_earnings or 0 for o in orders)
    manager_total = sum(o.manager_earnings or 0 for o in orders)
    
    return render_template('manager/payments.html',
                           orders=orders,
                           summary=summary,
                           total_orders=total_orders,
                           rider_total=rider_total,
                           manager_total=manager_total,
                           start_of_week=start_of_week,
                           end_of_week=end_of_week - timedelta(days=1),
                           weeks_ago=weeks_ago)


@manager_bp.route('/riders')
@login_required
@manager_required
@account_status_required
def riders():
    """View riders managed by this manager."""
    if not current_user.can_manage_riders():
        flash('You do not have permission to manage riders.', 'error')
        return redirect(url_for('manager.dashboard'))
    
    if current_user.manager_type == 'head':
        riders = Rider.query.all()
    else:
        riders = current_user.managed_riders.all()
    return render_template('manager/riders.html', riders=riders)


@manager_bp.route('/riders/create', methods=['GET', 'POST'])
@login_required
@manager_required
@account_status_required
def create_rider():
    """Create a new rider account."""
    if not current_user.can_manage_riders():
        flash('You do not have permission to manage riders.', 'error')
        return redirect(url_for('manager.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email') or None
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        password = request.form.get('password')

        # Validation
        if not all([full_name, phone_number, password, address]):
            flash('Please fill in all required fields.', 'error')
            return render_template('manager/create_rider.html')

        # Check if phone/email already exists
        if User.query.filter_by(phone_number=phone_number).first():
            flash('Phone number already registered.', 'error')
            return render_template('manager/create_rider.html')

        if email and User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('manager/create_rider.html')

        try:
            rider = Rider(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                address=address,
                manager_id=current_user.id
            )
            rider.set_password(password)

            db.session.add(rider)
            db.session.commit()

            flash('Rider created successfully!', 'success')
            return redirect(url_for('manager.riders'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating rider: {str(e)}', 'error')

    return render_template('manager/create_rider.html')


@manager_bp.route('/riders/<int:rider_id>/edit', methods=['GET', 'POST'])
@login_required
@manager_required
@account_status_required
def edit_rider(rider_id):
    """Edit rider account (for managers)."""
    if not current_user.can_manage_riders():
        flash('You do not have permission to manage riders.', 'error')
        return redirect(url_for('manager.dashboard'))
    
    rider = Rider.query.get_or_404(rider_id)
    
    # Check if this rider is managed by the current manager
    if rider.manager_id != current_user.id:
        flash('You can only edit riders assigned to you.', 'error')
        return redirect(url_for('manager.riders'))
    
    if request.method == 'POST':
        rider.full_name = request.form.get('full_name')
        rider.email = request.form.get('email') or None
        rider.phone_number = request.form.get('phone_number')
        rider.address = request.form.get('address')
        rider.is_active = request.form.get('is_active') == 'on'
        rider.is_available = request.form.get('is_available') == 'on'
        
        if request.form.get('password'):
            rider.set_password(request.form.get('password'))
        
        try:
            db.session.commit()
            flash('Rider updated successfully!', 'success')
            return redirect(url_for('manager.riders'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating rider: {str(e)}', 'error')
    
    return render_template('manager/edit_rider.html', rider=rider)


@manager_bp.route('/consumers')
@login_required
@manager_required
@account_status_required
def consumers():
    """View consumers managed by this manager."""
    if not current_user.can_manage_consumers():
        flash('You do not have permission to manage consumers.', 'error')
        return redirect(url_for('manager.dashboard'))
    
    if current_user.manager_type == 'head':
        consumers = Consumer.query.all()
    else:
        consumers = current_user.managed_consumers.all()
    # Calculate total orders to avoid template filter issues
    total_orders = sum(len(consumer.orders.all()) for consumer in consumers)
    return render_template('manager/consumers.html', consumers=consumers, total_orders=total_orders)


@manager_bp.route('/consumers/<int:consumer_id>/edit', methods=['GET', 'POST'])
@login_required
@manager_required
@account_status_required
def edit_consumer(consumer_id):
    """Edit consumer account (for managers)."""
    if not current_user.can_manage_consumers():
        flash('You do not have permission to manage consumers.', 'error')
        return redirect(url_for('manager.dashboard'))
    
    consumer = Consumer.query.get_or_404(consumer_id)
    
    # Check if this consumer is managed by the current manager
    if consumer.manager_id != current_user.id:
        flash('You can only edit consumers assigned to you.', 'error')
        return redirect(url_for('manager.consumers'))
    
    if request.method == 'POST':
        consumer.full_name = request.form.get('full_name')
        consumer.email = request.form.get('email') or None
        consumer.phone_number = request.form.get('phone_number')
        consumer.address = request.form.get('address')
        consumer.is_active = request.form.get('is_active') == 'on'
        
        if request.form.get('password'):
            consumer.set_password(request.form.get('password'))
        
        try:
            db.session.commit()
            flash('Consumer updated successfully!', 'success')
            return redirect(url_for('manager.consumers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating consumer: {str(e)}', 'error')
    
    return render_template('manager/edit_consumer.html', consumer=consumer)


# Account Status Management Routes
@manager_bp.route('/users/<int:user_id>/suspend', methods=['POST'])
@login_required
@manager_required
def suspend_user(user_id):
    """Suspend a user account."""
    try:
        # Check permissions - managers can only suspend users they manage
        if current_user.role_type == 'manager':
            user = User.query.get_or_404(user_id)
            if not user or (user.role_type == 'rider' and user.manager_id != current_user.id) or \
               (user.role_type == 'consumer' and user.manager_id != current_user.id):
                return jsonify({'success': False, 'error': 'You do not have permission to manage this user'}), 403
        else:
            # Admins can manage anyone
            user = User.query.get_or_404(user_id)
        
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')
        suspension_days = data.get('suspension_days')
        
        if suspension_days:
            from datetime import timedelta
            suspension_until = datetime.utcnow() + timedelta(days=int(suspension_days))
        else:
            suspension_until = None
        
        user.suspend_account(reason, suspension_until, current_user)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'User account suspended successfully',
            'status': 'suspended'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@manager_bp.route('/users/<int:user_id>/ban', methods=['POST'])
@login_required
@manager_required
def ban_user(user_id):
    """Ban a user account."""
    try:
        # Check permissions - managers can only ban users they manage
        if current_user.role_type == 'manager':
            user = User.query.get_or_404(user_id)
            if not user or (user.role_type == 'rider' and user.manager_id != current_user.id) or \
               (user.role_type == 'consumer' and user.manager_id != current_user.id):
                return jsonify({'success': False, 'error': 'You do not have permission to manage this user'}), 403
        else:
            # Admins can manage anyone
            user = User.query.get_or_404(user_id)
        
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')
        
        user.ban_account(reason, current_user)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'User account banned successfully',
            'status': 'banned'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@manager_bp.route('/users/<int:user_id>/reactivate', methods=['POST'])
@login_required
@manager_required
def reactivate_user(user_id):
    """Reactivate a suspended or banned user account."""
    try:
        # Check permissions - managers can only reactivate users they manage
        if current_user.role_type == 'manager':
            user = User.query.get_or_404(user_id)
            if not user or (user.role_type == 'rider' and user.manager_id != current_user.id) or \
               (user.role_type == 'consumer' and user.manager_id != current_user.id):
                return jsonify({'success': False, 'error': 'You do not have permission to manage this user'}), 403
        else:
            # Admins can manage anyone
            user = User.query.get_or_404(user_id)
        
        user.reactivate_account()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'User account reactivated successfully',
            'status': 'active'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
