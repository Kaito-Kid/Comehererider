"""
Admin routes for ComeHere Rider (CHR).
Handles administrator dashboard and management functions.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.utils.decorators import admin_required, account_status_required
from app import db
from app.models import Admin, Manager, Rider, Consumer, Order, Report, User, Document
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/accounts')
@login_required
@admin_required
@account_status_required
def accounts():
    """Comprehensive account management dashboard for administrators."""
    # Get account statistics
    from app.models import AccountAction
    
    # Calculate stats based on latest AccountAction for each user
    total_users = User.query.count()
    
    # Get active users (no ban/suspend actions or latest action is reactivate)
    active_users = []
    suspended_users = []
    banned_users = []
    
    all_users = User.query.all()
    for user in all_users:
        status = user.get_account_status()
        if status == 'active':
            active_users.append(user)
        elif status == 'suspended':
            suspended_users.append(user)
        elif status == 'banned':
            banned_users.append(user)
    
    account_stats = {
        'total_users': total_users,
        'total_active': len(active_users),
        'total_suspended': len(suspended_users),
        'total_banned': len(banned_users)
    }
    
    return render_template('admin/accounts.html',
                         account_stats=account_stats,
                         active_accounts=active_users,
                         suspended_accounts=suspended_users,
                         banned_accounts=banned_users)


@admin_bp.route('/dashboard')
@login_required
@account_status_required
@admin_required
@account_status_required
def dashboard():
    """Admin dashboard with system overview."""
    # Get system statistics
    total_managers = db.session.query(Manager).count()
    total_riders = db.session.query(Rider).count()
    total_consumers = db.session.query(Consumer).count()
    total_orders = db.session.query(Order).count()
    pending_reports = db.session.query(Report).filter_by(status='pending').count()
    
    return render_template('admin/dashboard.html',
                         total_managers=total_managers,
                         total_riders=total_riders,
                         total_consumers=total_consumers,
                         total_orders=total_orders,
                         pending_reports=pending_reports)


# Manager Management
@admin_bp.route('/managers')
@login_required
@account_status_required
@admin_required
@account_status_required
def managers():
    """View all managers with search and filtering capabilities."""
    # Get search and filter parameters
    search_query = request.args.get('search', '').strip()
    manager_type_filter = request.args.get('manager_type', '')
    status_filter = request.args.get('status', '')

    # Base query
    query = Manager.query

    # Apply search filters
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Manager.full_name.ilike(search_filter),
                Manager.email.ilike(search_filter),
                Manager.phone_number.ilike(search_filter)
            )
        )

    # Apply manager type filter
    if manager_type_filter:
        query = query.filter(Manager.manager_type == manager_type_filter)

    # Apply status filter
    if status_filter:
        if status_filter == 'active':
            query = query.filter(Manager.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(Manager.is_active == False)

    # Get filtered managers
    managers = query.all()

    # Prepare filter options for template
    filter_options = {
        'search': search_query,
        'manager_type': manager_type_filter,
        'status': status_filter,
        'total_count': len(managers),
        'has_filters': bool(search_query or manager_type_filter or status_filter)
    }

    return render_template('admin/managers.html', managers=managers, **filter_options)


@admin_bp.route('/managers/create', methods=['GET', 'POST'])
@login_required
@account_status_required
@admin_required
@account_status_required
def create_manager():
    """Create a new manager account."""
    if request.method == 'POST':
        manager_type = request.form.get('manager_type')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        password = request.form.get('password')
        address = request.form.get('address')
        
        # Validation
        if not all([manager_type, full_name, phone_number, password, address]):
            flash('Please fill in all required fields.', 'error')
            return render_template('admin/create_manager.html')
        
        # Check if phone/email already exists across all user types
        if User.query.filter_by(phone_number=phone_number).first():
            flash('Phone number already registered.', 'error')
            return render_template('admin/create_manager.html')
        
        if email and User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('admin/create_manager.html')
        
        try:
            manager = Manager(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                address=address,
                manager_type=manager_type
            )
            manager.set_password(password)
            manager.accept_terms()
            
            db.session.add(manager)
            db.session.commit()
            
            flash(f'{manager_type.title()} Manager created successfully!', 'success')
            return redirect(url_for('admin.managers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating manager: {str(e)}', 'error')
    
    return render_template('admin/create_manager.html')


@admin_bp.route('/managers/<int:manager_id>/edit', methods=['GET', 'POST'])
@login_required
@account_status_required
@admin_required
@account_status_required
def edit_manager(manager_id):
    """Edit manager account."""
    manager = Manager.query.get_or_404(manager_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            # Update profile information only
            manager.full_name = request.form.get('full_name')
            manager.email = request.form.get('email') or None
            manager.phone_number = request.form.get('phone_number')
            manager.address = request.form.get('address')
            manager.manager_type = request.form.get('manager_type')
            
            try:
                db.session.commit()
                flash('Manager profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating profile: {str(e)}', 'error')
                
        elif action == 'update_credentials':
            # Handle account status changes
            status_action = request.form.get('status_action')
            if status_action == 'suspend':
                suspension_reason = request.form.get('suspension_reason')
                suspension_days = request.form.get('suspension_days')
                if suspension_days:
                    from datetime import timedelta
                    suspension_until = datetime.utcnow() + timedelta(days=int(suspension_days))
                else:
                    suspension_until = None
                manager.suspend_account(suspension_reason, suspension_until, current_user)
                flash('Manager account suspended successfully!', 'warning')
            elif status_action == 'ban':
                ban_reason = request.form.get('ban_reason')
                manager.ban_account(ban_reason, current_user)
                flash('Manager account banned successfully!', 'danger')
            elif status_action == 'reactivate':
                manager.reactivate_account()
                flash('Manager account reactivated successfully!', 'success')
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating credentials: {str(e)}', 'error')
                
        elif action == 'change_password':
            # Change password with verification
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate current password
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('admin/edit_manager.html', manager=manager)
            
            # Validate new passwords
            if not new_password or new_password != confirm_password:
                flash('New passwords do not match or are empty.', 'error')
                return render_template('admin/edit_manager.html', manager=manager)
            
            if current_user.check_password(new_password):
                flash('New password must be different from current password.', 'error')
                return render_template('admin/edit_manager.html', manager=manager)
            
            try:
                manager.set_password(new_password)
                db.session.commit()
                flash('Manager password changed successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error changing password: {str(e)}', 'error')
        
        # Stay on the same page for accordion forms
        return render_template('admin/edit_manager.html', manager=manager)
    
    return render_template('admin/edit_manager.html', manager=manager)


@admin_bp.route('/managers/<int:manager_id>/delete', methods=['POST'])
@login_required
@account_status_required
@admin_required
def delete_manager(manager_id):
    """Delete manager account."""
    manager = Manager.query.get_or_404(manager_id)
    
    # Strict deletion policy: Only super admins can hard delete managers with assigned accounts
    has_managed = manager.managed_riders.count() > 0 or manager.managed_consumers.count() > 0
    if has_managed:
        admin = Admin.query.get(current_user.id)
        if admin.admin_level != 'super_admin':
            flash('Only super admins can delete managers with managed riders or consumers. Please deactivate the account instead.', 'error')
            return redirect(url_for('admin.managers'))

    try:
        db.session.delete(manager)
        db.session.commit()
        flash('Manager deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting manager: {str(e)}', 'error')
    
    return redirect(url_for('admin.managers'))


# Rider Management
@admin_bp.route('/riders')
@login_required
@account_status_required
@admin_required
def riders():
    """View all riders with search and filtering capabilities."""
    # Get search and filter parameters
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    availability_filter = request.args.get('availability', '')

    # Base query
    query = Rider.query

    # Apply search filters
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Rider.full_name.ilike(search_filter),
                Rider.email.ilike(search_filter),
                Rider.phone_number.ilike(search_filter)
            )
        )

    # Apply status filter
    if status_filter:
        if status_filter == 'active':
            query = query.filter(Rider.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(Rider.is_active == False)

    # Apply availability filter
    if availability_filter:
        if availability_filter == 'available':
            query = query.filter(Rider.is_available == True)
        elif availability_filter == 'unavailable':
            query = query.filter(Rider.is_available == False)

    # Get filtered riders
    riders = query.all()

    # Prepare filter options for template
    filter_options = {
        'search': search_query,
        'status': status_filter,
        'availability': availability_filter,
        'total_count': len(riders),
        'has_filters': bool(search_query or status_filter or availability_filter)
    }

    return render_template('admin/riders.html', riders=riders, **filter_options)


@admin_bp.route('/riders/create', methods=['GET', 'POST'])
@login_required
@account_status_required
@admin_required
def create_rider():
    """Create a new rider account."""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email') or None
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        password = request.form.get('password')
        
        # Admins can optionally assign a manager
        manager_id = request.form.get('manager_id')
        if manager_id and not manager_id.isdigit():
            manager_id = None
        elif manager_id:
            manager_id = int(manager_id)

        # Validation
        if not all([full_name, phone_number, password, address]):
            flash('Please fill in all required fields.', 'error')
            return render_template('admin/create_rider.html', managers=Manager.query.all())

        # Check if phone/email already exists
        if User.query.filter_by(phone_number=phone_number).first():
            flash('Phone number already registered.', 'error')
            return render_template('admin/create_rider.html', managers=Manager.query.all())

        if email and User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('admin/create_rider.html', managers=Manager.query.all())

        try:
            rider = Rider(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                address=address,
                manager_id=manager_id
            )
            rider.set_password(password)

            db.session.add(rider)
            db.session.commit()

            flash('Rider created successfully!', 'success')
            return redirect(url_for('admin.riders'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating rider: {str(e)}', 'error')

    # Fetch all active managers for assignment
    managers = Manager.query.filter_by(is_active=True).all()
    return render_template('admin/create_rider.html', managers=managers)


@admin_bp.route('/riders/<int:rider_id>/edit', methods=['GET', 'POST'])
@login_required
@account_status_required
@admin_required
def edit_rider(rider_id):
    """Edit rider account."""
    rider = Rider.query.get_or_404(rider_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            # Update profile information only
            rider.full_name = request.form.get('full_name')
            rider.email = request.form.get('email') or None
            rider.phone_number = request.form.get('phone_number')
            rider.address = request.form.get('address')
            
            try:
                db.session.commit()
                flash('Rider profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating profile: {str(e)}', 'error')
                
        elif action == 'update_credentials':
            # Handle account status changes
            status_action = request.form.get('status_action')
            if status_action == 'suspend':
                suspension_reason = request.form.get('suspension_reason')
                suspension_days = request.form.get('suspension_days')
                if suspension_days:
                    from datetime import timedelta
                    suspension_until = datetime.utcnow() + timedelta(days=int(suspension_days))
                else:
                    suspension_until = None
                rider.suspend_account(suspension_reason, suspension_until, current_user)
                flash('Rider account suspended successfully!', 'warning')
            elif status_action == 'ban':
                ban_reason = request.form.get('ban_reason')
                rider.ban_account(ban_reason, current_user)
                flash('Rider account banned successfully!', 'danger')
            elif status_action == 'reactivate':
                rider.reactivate_account()
                flash('Rider account reactivated successfully!', 'success')
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating credentials: {str(e)}', 'error')
                
        elif action == 'change_password':
            # Change password with verification
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate current password
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('admin/edit_rider.html', rider=rider)
            
            # Validate new passwords
            if not new_password or new_password != confirm_password:
                flash('New passwords do not match or are empty.', 'error')
                return render_template('admin/edit_rider.html', rider=rider)
            
            if current_user.check_password(new_password):
                flash('New password must be different from current password.', 'error')
                return render_template('admin/edit_rider.html', rider=rider)
            
            try:
                rider.set_password(new_password)
                db.session.commit()
                flash('Rider password changed successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error changing password: {str(e)}', 'error')
        
        # Stay on the same page for accordion forms
        return render_template('admin/edit_rider.html', rider=rider)
    
    return render_template('admin/edit_rider.html', rider=rider)


@admin_bp.route('/riders/<int:rider_id>/delete', methods=['POST'])
@login_required
@account_status_required
@admin_required
def delete_rider(rider_id):
    """Delete rider account."""
    rider = Rider.query.get_or_404(rider_id)
    
    # Strict deletion policy: Only super admins can hard delete riders with order history
    if rider.orders.count() > 0:
        admin = Admin.query.get(current_user.id)
        if admin.admin_level != 'super_admin':
            flash('Only super admins can delete riders with order history. Please deactivate the account instead.', 'error')
            return redirect(url_for('admin.riders'))

    try:
        db.session.delete(rider)
        db.session.commit()
        flash('Rider deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting rider: {str(e)}', 'error')
    
    return redirect(url_for('admin.riders'))


# Consumer Management
@admin_bp.route('/consumers')
@login_required
@account_status_required
@admin_required
def consumers():
    """View all consumers with search and filtering capabilities."""
    # Get search and filter parameters
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    registration_filter = request.args.get('registration', '')

    # Base query
    query = Consumer.query

    # Apply search filters
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Consumer.full_name.ilike(search_filter),
                Consumer.email.ilike(search_filter),
                Consumer.phone_number.ilike(search_filter)
            )
        )

    # Apply status filter
    if status_filter:
        if status_filter == 'active':
            query = query.filter(Consumer.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(Consumer.is_active == False)

    # Apply registration filter
    if registration_filter:
        if registration_filter == 'self_registered':
            query = query.filter(Consumer.manager_id.is_(None))
        elif registration_filter == 'manager_created':
            query = query.filter(Consumer.manager_id.isnot(None))

    # Get filtered consumers
    consumers = query.all()

    # Calculate total orders to avoid template filter issues
    total_orders = sum(len(consumer.orders.all()) for consumer in consumers)

    # Prepare filter options for template
    filter_options = {
        'search': search_query,
        'status': status_filter,
        'registration': registration_filter,
        'total_count': len(consumers),
        'has_filters': bool(search_query or status_filter or registration_filter)
    }

    return render_template('admin/consumers.html', consumers=consumers, total_orders=total_orders, **filter_options)


@admin_bp.route('/consumers/<int:consumer_id>/edit', methods=['GET', 'POST'])
@login_required
@account_status_required
@admin_required
def edit_consumer(consumer_id):
    """Edit consumer account."""
    consumer = Consumer.query.get_or_404(consumer_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            # Update profile information only
            consumer.full_name = request.form.get('full_name')
            consumer.email = request.form.get('email') or None
            consumer.phone_number = request.form.get('phone_number')
            consumer.address = request.form.get('address')
            
            try:
                db.session.commit()
                flash('Consumer profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating profile: {str(e)}', 'error')
                
        elif action == 'update_credentials':
            # Handle account status changes
            status_action = request.form.get('status_action')
            if status_action == 'suspend':
                suspension_reason = request.form.get('suspension_reason')
                suspension_days = request.form.get('suspension_days')
                if suspension_days:
                    from datetime import timedelta
                    suspension_until = datetime.utcnow() + timedelta(days=int(suspension_days))
                else:
                    suspension_until = None
                consumer.suspend_account(suspension_reason, suspension_until, current_user)
                flash('Consumer account suspended successfully!', 'warning')
            elif status_action == 'ban':
                ban_reason = request.form.get('ban_reason')
                consumer.ban_account(ban_reason, current_user)
                flash('Consumer account banned successfully!', 'danger')
            elif status_action == 'reactivate':
                consumer.reactivate_account()
                flash('Consumer account reactivated successfully!', 'success')
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating credentials: {str(e)}', 'error')
                
        elif action == 'change_password':
            # Change password with verification
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate current password
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('admin/edit_consumer.html', consumer=consumer)
            
            # Validate new passwords
            if not new_password or new_password != confirm_password:
                flash('New passwords do not match or are empty.', 'error')
                return render_template('admin/edit_consumer.html', consumer=consumer)
            
            if current_user.check_password(new_password):
                flash('New password must be different from current password.', 'error')
                return render_template('admin/edit_consumer.html', consumer=consumer)
            
            try:
                consumer.set_password(new_password)
                db.session.commit()
                flash('Consumer password changed successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error changing password: {str(e)}', 'error')
        
        # Stay on the same page for accordion forms
        return render_template('admin/edit_consumer.html', consumer=consumer)
    
    return render_template('admin/edit_consumer.html', consumer=consumer)


@admin_bp.route('/consumers/<int:consumer_id>/delete', methods=['POST'])
@login_required
@admin_required
@account_status_required
def delete_consumer(consumer_id):
    """Delete consumer account."""
    consumer = Consumer.query.get_or_404(consumer_id)
    
    # Strict deletion policy: Only super admins can hard delete users with order history
    if consumer.orders.count() > 0:
        admin = Admin.query.get(current_user.id)
        if admin.admin_level != 'super_admin':
            flash('Only super admins can delete consumers with order history. Please deactivate the account instead.', 'error')
            return redirect(url_for('admin.consumers'))

    try:
        db.session.delete(consumer)
        db.session.commit()
        flash('Consumer deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting consumer: {str(e)}', 'error')
    
    return redirect(url_for('admin.consumers'))


# Account Status Management Routes for Admins
@admin_bp.route('/users/<int:user_id>/view')
@login_required
@admin_required
@account_status_required
def view_user_profile(user_id):
    """View any user's profile (admin access)."""
    user = User.query.get_or_404(user_id)

    # Get latest account action for status details
    from app.models import AccountAction
    latest_action = AccountAction.query.filter_by(user_id=user_id)\
        .order_by(AccountAction.created_at.desc()).first()

    # Build profile data similar to API
    profile_data = {
        'id': user.id,
        'full_name': user.full_name,
        'email': user.email,
        'phone_number': user.phone_number,
        'address': user.address,
        'role_type': user.role_type,
        'profile_picture': user.profile_picture,
        'account_status': user.get_account_status_display(),
        'account_status_code': user.get_account_status(),
        'is_active': user.is_account_active(),
        'member_since': user.created_at.strftime('%B %Y'),
        'last_updated': user.updated_at.strftime('%B %d, %Y'),
        'last_login': user.last_login.strftime('%B %d, %Y at %I:%M %p') if user.last_login else 'Never'
    }

    # Add suspension/ban details if applicable from latest action
    if latest_action and latest_action.action_type == 'suspend':
        profile_data.update({
            'suspension_reason': latest_action.reason,
            'suspension_until': latest_action.suspension_until.strftime('%B %d, %Y at %I:%M %p') if latest_action.suspension_until else None
        })
    elif latest_action and latest_action.action_type == 'ban':
        profile_data.update({
            'ban_reason': latest_action.reason,
            'banned_at': latest_action.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'banned_by': latest_action.performed_by.full_name if latest_action.performed_by else 'Unknown'
        })

    # Add role-specific data
    if user.role_type == 'rider':
        rider = Rider.query.get(user_id)
        if rider:
            profile_data.update({
                'is_available': rider.is_available,
                'total_orders_completed': rider.total_orders_completed,
                'average_rating': rider.average_rating,
                'total_earnings': rider.total_earnings
            })
    elif user.role_type == 'consumer':
        consumer = Consumer.query.get(user_id)
        if consumer:
            profile_data.update({
                'total_orders_placed': consumer.total_orders_placed,
                'default_address': consumer.default_address
            })
    elif user.role_type == 'manager':
        manager = Manager.query.get(user_id)
        if manager:
            profile_data.update({
                'manager_type': manager.manager_type,
                'can_manage_riders': manager.can_manage_riders(),
                'can_manage_consumers': manager.can_manage_consumers(),
                'managed_riders': manager.managed_riders,
                'managed_consumers': manager.managed_consumers
            })

    # Get user documents
    documents = Document.query.filter_by(user_id=user_id).order_by(Document.uploaded_at.desc()).all()

    return render_template('admin/view_profile.html', profile=profile_data, documents=documents)


@admin_bp.route('/users/<int:user_id>/suspend', methods=['POST'])
@login_required
@admin_required
def suspend_user_admin(user_id):
    """Suspend any user account (admin access)."""
    try:
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


@admin_bp.route('/users/<int:user_id>/ban', methods=['POST'])
@login_required
@admin_required
def ban_user_admin(user_id):
    """Ban any user account (admin access)."""
    try:
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


@admin_bp.route('/users/<int:user_id>/reactivate', methods=['POST'])
@login_required
@admin_required
def reactivate_user_admin(user_id):
    """Reactivate any suspended or banned user account (admin access)."""
    try:
        user = User.query.get_or_404(user_id)

        user.reactivate_account(current_user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'User account reactivated successfully',
            'status': 'active'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/edit-profile', methods=['POST'])
@login_required
@admin_required
@account_status_required
def edit_user_profile_admin(user_id):
    """Edit any user's profile information (admin access)."""
    try:
        user = User.query.get_or_404(user_id)

        data = request.get_json() or {}
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip() or None
        phone_number = data.get('phone_number', '').strip()
        address = data.get('address', '').strip()

        # Validation
        if not full_name or not phone_number or not address:
            return jsonify({'success': False, 'error': 'Full name, phone number, and address are required'}), 400

        # Update user information
        user.full_name = full_name
        user.email = email
        user.phone_number = phone_number
        user.address = address

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
@account_status_required
def reset_user_password_admin(user_id):
    """Reset any user's password (admin access)."""
    try:
        user = User.query.get_or_404(user_id)

        data = request.get_json() or {}
        new_password = data.get('new_password', '').strip()
        admin_password = data.get('admin_password', '').strip()

        # Validation
        if not admin_password:
            return jsonify({'success': False, 'error': 'Admin password is required for verification'}), 400
            
        if not current_user.check_password(admin_password):
            return jsonify({'success': False, 'error': 'Incorrect admin password'}), 401

        if not new_password or len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters long'}), 400

        # Update password
        user.set_password(new_password)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Password reset successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
@account_status_required
def delete_user_admin(user_id):
    """Delete any user account (admin access)."""
    try:
        user = User.query.get_or_404(user_id)

        # Prevent deletion of admin accounts for safety
        if user.role_type == 'admin':
            return jsonify({'success': False, 'error': 'Admin accounts cannot be deleted'}), 400

        # Store user info for confirmation
        user_info = f"{user.full_name} ({user.role_type})"

        db.session.delete(user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'User account {user_info} deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# Reports Management
@admin_bp.route('/reports')
@login_required
@account_status_required
@admin_required
def reports():
    """View all reports."""
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template('admin/reports.html', reports=reports)


@admin_bp.route('/reports/<int:report_id>/handle', methods=['GET', 'POST'])
@login_required
@account_status_required
@admin_required
def handle_report(report_id):
    """Handle a bug report."""
    report = Report.query.get_or_404(report_id)
    
    if request.method == 'POST':
        report.status = request.form.get('status')
        report.handler_id = current_user.id
        report.handled_at = datetime.utcnow()
        report.resolution_notes = request.form.get('resolution_notes')
        
        try:
            db.session.commit()
            flash('Report handled successfully!', 'success')
            return redirect(url_for('admin.reports'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error handling report: {str(e)}', 'error')
    
    return render_template('admin/handle_report.html', report=report)


# System Logs
@admin_bp.route('/logs')
@login_required
@account_status_required
@admin_required
def system_logs():
    """View system logs."""
    import os
    from flask import current_app
    
    log_dir = current_app.config.get('LOG_DIR', 'logs')
    log_files = []
    
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(log_dir, filename)
                log_files.append({
                    'name': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath))
                })
    
    log_files.sort(key=lambda x: x['modified'], reverse=True)
    return render_template('admin/logs.html', log_files=log_files)


@admin_bp.route('/logs/view/<filename>')
@login_required
@account_status_required
@admin_required
def view_log(filename):
    """View contents of a specific log file."""
    import os
    from flask import current_app
    
    log_dir = current_app.config.get('LOG_DIR', 'logs')
    filepath = os.path.join(log_dir, filename)
    
    if not os.path.exists(filepath) or not filename.endswith('.log'):
        flash('Log file not found.', 'error')
        return redirect(url_for('admin.system_logs'))
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Get last 1000 lines to avoid huge page loads
        lines = content.split('\n')[-1000:]
        content = '\n'.join(lines)
        
        return render_template('admin/view_log.html', filename=filename, content=content)
    except Exception as e:
        flash(f'Error reading log file: {str(e)}', 'error')
        return redirect(url_for('admin.system_logs'))


@admin_bp.route('/profile')
@login_required
@account_status_required
@admin_required
def profile():
    """View admin profile."""
    return render_template('admin/profile.html')


@admin_bp.route('/settings')
@login_required
@account_status_required
@admin_required
def settings():
    """Admin settings page."""
    return render_template('admin/settings.html')
