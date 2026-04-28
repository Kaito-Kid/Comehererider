"""
Order models for ComeHere Rider (CHR).
Defines Order and OrderItem models for delivery management.
"""
from datetime import datetime
from app import db


class Order(db.Model):
    """
    Order model for delivery orders placed by consumers.
    """
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    consumer_id = db.Column(db.Integer, db.ForeignKey('consumers.id'), nullable=False)
    rider_id = db.Column(db.Integer, db.ForeignKey('riders.id'), nullable=True)
    
    # Order details
    store_name = db.Column(db.String(200), nullable=False)
    destination_address = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text)
    
    # Order status
    status = db.Column(db.String(50), default='pending')  # pending, accepted, in_progress, completed, cancelled
    rider_selection_method = db.Column(db.String(50))  # auto, manual_favorite, wait
    
    # Commission and payment
    base_commission = db.Column(db.Float, default=40.0)  # Base Php 40
    extra_commission = db.Column(db.Float, default=0.0)  # Additional charges
    total_commission = db.Column(db.Float)
    rider_earnings = db.Column(db.Float)  # Calculated: base 25 + extra 20
    manager_earnings = db.Column(db.Float)  # Calculated: base 15 + extra 10
    
    # Ratings
    consumer_rating = db.Column(db.Integer)  # Consumer rates rider (1-5)
    rider_rating = db.Column(db.Integer)  # Rider rates consumer (1-5)
    consumer_feedback = db.Column(db.Text)
    rider_feedback = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_commission(self):
        """
        Calculate commission split based on plan.md rules:
        - Base: Php 40 (Rider: 25, Manager: 15)
        - Extra: Php 30 per increment (Rider: 20, Manager: 10)
        """
        self.total_commission = self.base_commission + self.extra_commission
        
        # Calculate rider and manager earnings
        base_rider = 25.0
        base_manager = 15.0
        
        if self.extra_commission > 0:
            # Each Php 30 extra adds 20 to rider, 10 to manager
            extra_increments = self.extra_commission / 30.0
            extra_rider = extra_increments * 20.0
            extra_manager = extra_increments * 10.0
            
            self.rider_earnings = base_rider + extra_rider
            self.manager_earnings = base_manager + extra_manager
        else:
            self.rider_earnings = base_rider
            self.manager_earnings = base_manager
    
    def accept_order(self, rider):
        """Mark order as accepted by a rider."""
        self.rider_id = rider.id
        self.status = 'accepted'
        self.accepted_at = datetime.utcnow()
    
    def update_status(self, new_status):
        """Update order status with appropriate timestamps."""
        self.status = new_status
        if new_status == 'completed':
            self.completed_at = datetime.utcnow()
        elif new_status == 'cancelled':
            self.cancelled_at = datetime.utcnow()
    
    def can_cancel(self):
        """Check if order can be cancelled (only before rider accepts)."""
        return self.status == 'pending' and self.rider_id is None
    
    def __repr__(self):
        return f'<Order {self.id} - {self.status}>'


class OrderItem(db.Model):
    """
    OrderItem model for individual items in an order.
    """
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    # Item details
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    estimated_price = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<OrderItem {self.item_name} x{self.quantity}>'
