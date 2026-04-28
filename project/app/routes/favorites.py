"""
Favorites management routes for ComeHere Rider (CHR).
Allows consumers to manage their favorite riders.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Rider
from app.utils.decorators import consumer_required

favorites_bp = Blueprint('favorites', __name__, url_prefix='/favorites')


@favorites_bp.route('/')
@login_required
@consumer_required
def list():
    """List consumer's favorite riders."""
    favorites = current_user.favorite_riders
    return render_template('user/favorites.html', favorites=favorites)


@favorites_bp.route('/add/<int:rider_id>', methods=['POST'])
@login_required
@consumer_required
def add(rider_id):
    """Add a rider to favorites."""
    rider = Rider.query.get_or_404(rider_id)
    
    if rider in current_user.favorite_riders:
        flash('Rider is already in your favorites.', 'info')
    else:
        current_user.add_favorite_rider(rider)
        db.session.commit()
        flash(f'{rider.full_name} added to favorites!', 'success')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': 'Added to favorites'})
    
    return redirect(request.referrer or url_for('user.dashboard'))


@favorites_bp.route('/remove/<int:rider_id>', methods=['POST'])
@login_required
@consumer_required
def remove(rider_id):
    """Remove a rider from favorites."""
    rider = Rider.query.get_or_404(rider_id)
    
    if rider not in current_user.favorite_riders:
        flash('Rider is not in your favorites.', 'info')
    else:
        current_user.remove_favorite_rider(rider)
        db.session.commit()
        flash(f'{rider.full_name} removed from favorites.', 'info')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': 'Removed from favorites'})
    
    return redirect(url_for('favorites.list'))
