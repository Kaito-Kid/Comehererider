"""
Order management routes for ComeHere Rider (CHR).
Handles order creation, tracking, and management for consumers and riders.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db, limiter
from app.models import Order, OrderItem, Rider, Consumer
from app.utils.decorators import consumer_required, rider_required

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


@orders_bp.route('/create', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
@login_required
@consumer_required
def create():
    """
    Create new order page for consumers.
    Per plan.md: User enters destination, store name, items, instructions.
    """
    if request.method == 'POST':
        try:
            # Get form data
            destination_address = request.form.get('destination_address')
            use_default_address = request.form.get('use_default_address') == 'on'
            store_name = request.form.get('store_name')
            instructions = request.form.get('instructions', '')
            rider_selection = request.form.get('rider_selection', 'wait')  # wait, auto, manual
            
            # Use default address if checked
            if use_default_address:
                destination_address = current_user.default_address
            
            if not all([destination_address, store_name]):
                flash('Please provide destination address and store name.', 'error')
                return render_template('user/create_order.html')
            
            # Create order
            order = Order(
                consumer_id=current_user.id,
                store_name=store_name,
                destination_address=destination_address,
                instructions=instructions,
                rider_selection_method=rider_selection,
                status='pending'
            )
            
            # Set commission (base Php 40)
            order.base_commission = 40.0
            order.extra_commission = 0.0
            
            # Get items
            item_names = request.form.getlist('item_name[]')
            item_quantities = request.form.getlist('item_quantity[]')
            item_prices = request.form.getlist('item_price[]')
            
            # Add extra commission based on number of items (per plan.md)
            if len(item_names) > 5:
                # More items = extra charge
                extra_increments = (len(item_names) - 5) // 3  # Every 3 extra items
                order.extra_commission = extra_increments * 30.0
            
            order.calculate_commission()
            
            db.session.add(order)
            db.session.flush()  # Get order ID
            
            # Add order items
            for name, qty, price in zip(item_names, item_quantities, item_prices):
                if name and qty:
                    item = OrderItem(
                        order_id=order.id,
                        item_name=name,
                        quantity=int(qty),
                        estimated_price=float(price) if price else 0.0
                    )
                    db.session.add(item)
            
            db.session.commit()
            
            # Update consumer stats
            current_user.total_orders_placed += 1
            db.session.commit()
            
            flash(f'Order created successfully! Commission: ₱{order.total_commission:.2f}', 'success')
            return redirect(url_for('orders.detail', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to create order: {str(e)}', 'error')
    
    # Get favorite riders for manual selection
    favorite_riders = current_user.favorite_riders
    
    return render_template('user/create_order.html', favorite_riders=favorite_riders)


@orders_bp.route('/<int:order_id>')
@login_required
def detail(order_id):
    """View order details."""
    order = Order.query.get_or_404(order_id)
    
    # Check permissions
    if current_user.role_type == 'consumer' and order.consumer_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('user.dashboard'))
    
    if current_user.role_type == 'rider':
        # Riders can view if:
        # 1. Order is pending (available to all)
        # 2. They are the assigned rider
        if order.status != 'pending' and order.rider_id != current_user.id:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('rider.dashboard'))
    
    return render_template('orders/detail.html', order=order)


@orders_bp.route('/history')
@login_required
def history():
    """View order history for current user."""
    if current_user.role_type == 'consumer':
        orders = current_user.orders.order_by(Order.created_at.desc()).all()
        return render_template('user/order_history.html', orders=orders)
    elif current_user.role_type == 'rider':
        orders = current_user.orders.order_by(Order.created_at.desc()).all()
        return render_template('rider/order_history.html', orders=orders)
    else:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))


@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@login_required
@consumer_required
def cancel(order_id):
    """
    Cancel an order (only before rider accepts).
    Per plan.md: Users can cancel only if order not yet accepted.
    """
    order = Order.query.get_or_404(order_id)
    
    if order.consumer_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('user.dashboard'))
    
    if order.can_cancel():
        order.update_status('cancelled')
        db.session.commit()
        flash('Order cancelled successfully.', 'success')
    else:
        flash('Cannot cancel order after rider has accepted.', 'error')
    
    return redirect(url_for('orders.detail', order_id=order.id))


@orders_bp.route('/<int:order_id>/accept', methods=['POST'])
@login_required
@rider_required
def accept(order_id):
    """
    Rider accepts an order.
    Per plan.md: Riders can accept pending orders.
    """
    order = Order.query.get_or_404(order_id)
    
    if order.status != 'pending':
        flash('Order is no longer available.', 'error')
        return redirect(url_for('rider.dashboard'))
    
    if order.rider_id and order.rider_id != current_user.id:
        flash('Order already assigned to another rider.', 'error')
        return redirect(url_for('rider.dashboard'))
    
    order.accept_order(current_user)
    db.session.commit()
    
    flash('Order accepted! Start delivering.', 'success')
    return redirect(url_for('orders.manage', order_id=order.id))


@orders_bp.route('/<int:order_id>/reject', methods=['POST'])
@login_required
@rider_required
def reject(order_id):
    """Rider rejects an order."""
    order = Order.query.get_or_404(order_id)
    
    if order.rider_id == current_user.id:
        order.rider_id = None
        order.status = 'pending'
        db.session.commit()
        flash('Order rejected.', 'info')
    
    return redirect(url_for('rider.dashboard'))


@orders_bp.route('/<int:order_id>/manage', methods=['GET', 'POST'])
@login_required
@rider_required
def manage(order_id):
    """
    Rider manages accepted order (update status).
    Per plan.md: Riders update order progress.
    """
    order = Order.query.get_or_404(order_id)
    
    if order.rider_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('rider.dashboard'))
    
    if request.method == 'POST':
        new_status = request.form.get('status')
        
        if new_status in ['in_progress', 'completed']:
            order.update_status(new_status)
            
            if new_status == 'completed':
                # Update rider stats
                current_user.total_orders_completed += 1
                current_user.total_earnings += order.rider_earnings
            
            db.session.commit()
            flash(f'Order status updated to {new_status}.', 'success')
            
            if new_status == 'completed':
                return redirect(url_for('orders.rate', order_id=order.id, role='rider'))
    
    return render_template('rider/manage_order.html', order=order)


@orders_bp.route('/<int:order_id>/rate', methods=['GET', 'POST'])
@login_required
def rate(order_id):
    """
    Rate order (consumer rates rider, rider rates consumer).
    Per plan.md: Both parties can rate each other after completion.
    """
    order = Order.query.get_or_404(order_id)
    
    if order.status != 'completed':
        flash('Can only rate completed orders.', 'error')
        return redirect(url_for('orders.detail', order_id=order.id))
    
    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        feedback = request.form.get('feedback', '')
        
        if current_user.role_type == 'consumer' and order.consumer_id == current_user.id:
            order.consumer_rating = rating
            order.consumer_feedback = feedback
            
            # Update rider's average rating
            if order.rider:
                order.rider.update_rating(rating)
            
            flash('Thank you for rating!', 'success')
            
        elif current_user.role_type == 'rider' and order.rider_id == current_user.id:
            order.rider_rating = rating
            order.rider_feedback = feedback
            flash('Thank you for rating!', 'success')
        
        db.session.commit()
        return redirect(url_for('orders.detail', order_id=order.id))
    
    return render_template('orders/rate.html', order=order)


@orders_bp.route('/available')
@login_required
@rider_required
def available():
    """
    View available orders for riders to accept.
    Shows pending orders based on selection method.
    """
    # Get pending orders
    pending_orders = Order.query.filter_by(status='pending').order_by(Order.created_at.desc()).all()
    
    return render_template('rider/available_orders.html', orders=pending_orders)


@orders_bp.route('/<int:order_id>/track')
@login_required
def track(order_id):
    """
    Track order in real-time.
    Per plan.md: Users track orders with live location updates.
    """
    order = Order.query.get_or_404(order_id)
    
    if current_user.role_type == 'consumer' and order.consumer_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('user.dashboard'))
    
    return render_template('orders/track.html', order=order)


@orders_bp.route('/<int:order_id>/location')
@limiter.limit("50 per minute")
@login_required
def get_location(order_id):
    """
    API endpoint to get rider's current location for tracking.
    Returns JSON with latitude/longitude.
    """
    order = Order.query.get_or_404(order_id)
    
    if not order.rider:
        return jsonify({'error': 'No rider assigned'}), 404
    
    return jsonify({
        'latitude': order.rider.current_latitude,
        'longitude': order.rider.current_longitude,
        'last_update': order.rider.last_location_update.isoformat() if order.rider.last_location_update else None,
        'status': order.status
    })


@orders_bp.route('/<int:order_id>/status')
@limiter.limit("100 per minute")
@login_required
def status(order_id):
    """
    Lightweight polling endpoint to get current order status.
    """
    order = Order.query.get_or_404(order_id)
    
    # Permissions: consumers can see own orders; riders see assigned orders
    if current_user.role_type == 'consumer' and order.consumer_id != current_user.id:
        return jsonify({'error': 'forbidden'}), 403
    if current_user.role_type == 'rider' and order.rider_id != current_user.id:
        return jsonify({'error': 'forbidden'}), 403
    
    return jsonify({'status': order.status})
