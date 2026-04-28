"""
API routes for profile data and analytics.
Provides JSON endpoints for fetching role-specific profile information.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Admin, Manager, Rider, Consumer, Order
from sqlalchemy import func, desc
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/profile/analytics')
@login_required
def profile_analytics():
    """Get role-specific analytics data for the current user."""
    try:
        analytics = {}
        
        if current_user.role_type == 'rider':
            rider = Rider.query.get(current_user.id)
            if rider:
                # Get completed orders count
                completed_orders = Order.query.filter_by(
                    rider_id=rider.id, 
                    status='completed'
                ).count()
                
                # Get earnings this month
                current_month = datetime.now().replace(day=1)
                monthly_earnings = db.session.query(func.sum(Order.rider_earnings)).filter(
                    Order.rider_id == rider.id,
                    Order.status == 'completed',
                    Order.completed_at >= current_month
                ).scalar() or 0
                
                # Get on-time delivery percentage
                total_completed = completed_orders
                on_time_count = Order.query.filter_by(
                    rider_id=rider.id,
                    status='completed'
                ).filter(
                    Order.completed_at <= Order.accepted_at + timedelta(hours=2)
                ).count()
                
                on_time_percentage = (on_time_count / total_completed * 100) if total_completed > 0 else 0
                
                analytics = {
                    'deliveries_completed': completed_orders,
                    'average_rating': round(rider.average_rating, 1),
                    'monthly_earnings': round(monthly_earnings, 2),
                    'on_time_percentage': round(on_time_percentage)
                }
                
        elif current_user.role_type == 'consumer':
            consumer = Consumer.query.get(current_user.id)
            if consumer:
                # Get orders placed
                orders_placed = Order.query.filter_by(consumer_id=consumer.id).count()
                
                # Get average rating given to riders
                avg_rating = db.session.query(func.avg(Order.consumer_rating)).filter(
                    Order.consumer_id == consumer.id,
                    Order.consumer_rating.isnot(None)
                ).scalar() or 0
                
                # Get total spent
                total_spent = db.session.query(func.sum(Order.total_commission)).filter(
                    Order.consumer_id == consumer.id,
                    Order.status == 'completed'
                ).scalar() or 0
                
                # Get favorite riders count
                favorite_riders_count = len(consumer.favorite_riders)
                
                analytics = {
                    'orders_placed': orders_placed,
                    'average_rating': round(avg_rating, 1),
                    'total_spent': round(total_spent, 2),
                    'favorite_riders': favorite_riders_count
                }
                
        elif current_user.role_type == 'manager':
            manager = Manager.query.get(current_user.id)
            if manager:
                # Get accounts managed
                accounts_managed = 0
                if manager.can_manage_riders():
                    accounts_managed += manager.managed_riders.count()
                if manager.can_manage_consumers():
                    accounts_managed += manager.managed_consumers.count()
                
                # Get orders processed (orders from managed accounts)
                orders_processed = 0
                if manager.can_manage_riders():
                    rider_ids = [r.id for r in manager.managed_riders]
                    orders_processed += Order.query.filter(Order.rider_id.in_(rider_ids)).count()
                
                # System uptime (placeholder - would be calculated from system metrics)
                system_uptime = 98
                
                # Performance rank (placeholder - would be calculated from manager metrics)
                performance_rank = 1
                
                analytics = {
                    'accounts_managed': accounts_managed,
                    'orders_processed': orders_processed,
                    'system_uptime': system_uptime,
                    'performance_rank': performance_rank
                }
                
        elif current_user.role_type == 'admin':
            # Get total system statistics
            total_users = User.query.count()
            total_orders = Order.query.count()
            completed_orders = Order.query.filter_by(status='completed').count()
            
            # System uptime (placeholder)
            system_uptime = 99
            
            analytics = {
                'total_users': total_users,
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'system_uptime': system_uptime
            }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/profile/security')
@login_required
def profile_security():
    """Get security information for the current user."""
    try:
        # Calculate password strength (placeholder - would use actual password analysis)
        password_strength = 85
        
        # Get last login (placeholder - would be tracked in database)
        last_login = current_user.last_login or datetime.now()
        
        # Get latest account action for status details
        from app.models import AccountAction
        latest_action = AccountAction.query.filter_by(user_id=current_user.id)\
            .order_by(AccountAction.created_at.desc()).first()
        
        security_info = {
            'account_status': current_user.get_account_status_display(),
            'account_status_code': current_user.get_account_status(),
            'last_login': last_login.strftime('%B %d, %Y at %I:%M %p'),
            'password_strength': password_strength,
            'two_factor_enabled': False,  # Placeholder for future implementation
            'username': current_user.phone_number,
            'login_method': 'Phone Number + Password',
            'recovery_available': bool(current_user.email)
        }
        
        # Add suspension/ban details if applicable from latest action
        if latest_action and latest_action.action_type == 'suspend':
            security_info.update({
                'suspension_reason': latest_action.reason,
                'suspension_until': latest_action.suspension_until.strftime('%B %d, %Y at %I:%M %p') if latest_action.suspension_until else None
            })
        elif latest_action and latest_action.action_type == 'ban':
            security_info.update({
                'ban_reason': latest_action.reason,
                'banned_at': latest_action.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'banned_by': latest_action.performed_by.full_name if latest_action.performed_by else 'Unknown'
            })
        
        return jsonify({
            'success': True,
            'security': security_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/profile/basic')
@login_required
def profile_basic():
    """Get basic profile information for the current user."""
    try:
        profile_info = {
            'id': current_user.id,
            'full_name': current_user.full_name,
            'email': current_user.email,
            'phone_number': current_user.phone_number,
            'address': current_user.address,
            'role_type': current_user.role_type,
            'profile_picture': current_user.profile_picture,
            'account_status': current_user.get_account_status_display(),
            'account_status_code': current_user.get_account_status(),
            'is_active': current_user.is_account_active(),
            'member_since': current_user.created_at.strftime('%B %Y'),
            'last_updated': current_user.updated_at.strftime('%B %d, %Y')
        }
        
        return jsonify({
            'success': True,
            'profile': profile_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/profile/<int:user_id>')
@login_required
def get_user_profile(user_id):
    """Get profile information for a specific user (manager access only)."""
    try:
        # Check if current user is a manager or admin
        if current_user.role_type not in ['manager', 'admin']:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access'
            }), 403
        
        # Get the target user
        target_user = User.query.get_or_404(user_id)
        
        # Check if manager can access this user
        if current_user.role_type == 'manager':
            manager = Manager.query.get(current_user.id)
            can_access = False
            
            if target_user.role_type == 'rider' and manager.can_manage_riders():
                rider = Rider.query.get(user_id)
                can_access = rider and rider.manager_id == manager.id
            elif target_user.role_type == 'consumer' and manager.can_manage_consumers():
                consumer = Consumer.query.get(user_id)
                can_access = consumer and consumer.manager_id == manager.id
            
            if not can_access:
                return jsonify({
                    'success': False,
                    'error': 'Cannot access this user profile'
                }), 403
        
        # Get latest account action for status details
        from app.models import AccountAction
        latest_action = AccountAction.query.filter_by(user_id=target_user.id)\
            .order_by(AccountAction.created_at.desc()).first()
        
        # Build profile data
        profile_data = {
            'id': target_user.id,
            'full_name': target_user.full_name,
            'email': target_user.email,
            'phone_number': target_user.phone_number,
            'address': target_user.address,
            'role_type': target_user.role_type,
            'profile_picture': target_user.profile_picture,
            'account_status': target_user.get_account_status_display(),
            'account_status_code': target_user.get_account_status(),
            'is_active': target_user.is_account_active(),
            'member_since': target_user.created_at.strftime('%B %Y'),
            'last_updated': target_user.updated_at.strftime('%B %d, %Y'),
            'last_login': target_user.last_login.strftime('%B %d, %Y at %I:%M %p') if target_user.last_login else 'Never'
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
        if target_user.role_type == 'rider':
            rider = Rider.query.get(user_id)
            if rider:
                profile_data.update({
                    'is_available': rider.is_available,
                    'total_orders_completed': rider.total_orders_completed,
                    'average_rating': rider.average_rating,
                    'total_earnings': rider.total_earnings
                })
        elif target_user.role_type == 'consumer':
            consumer = Consumer.query.get(user_id)
            if consumer:
                profile_data.update({
                    'total_orders_placed': consumer.total_orders_placed,
                    'default_address': consumer.default_address
                })
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
