"""
User models for ComeHere Rider (CHR).
Defines User base class and role-specific models (Admin, Manager, Rider, Consumer).
"""
from datetime import datetime
from flask_login import UserMixin
from app import db, bcrypt


class User(UserMixin, db.Model):
    """
    Base User model for all user types.
    Uses single table inheritance with discriminator column for role types.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    role_type = db.Column(db.String(50))  # Discriminator: admin, manager, rider, consumer
    
    # Basic information
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal details
    gender = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    address = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))
    
    # Account status - now computed from AccountAction history
    # No longer stored in User table, computed dynamically
    
    # Legacy field - keep for backward compatibility
    is_active = db.Column(db.Boolean, default=True)
    terms_accepted = db.Column(db.Boolean, default=False)
    privacy_accepted = db.Column(db.Boolean, default=False)
    terms_accepted_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    reports_made = db.relationship('Report', foreign_keys='Report.reporter_id', backref='reporter', lazy='dynamic', cascade='all, delete-orphan')
    reports_received = db.relationship('Report', foreign_keys='Report.reported_user_id', backref='reported_user', lazy='dynamic')
    
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': role_type
    }
    
    def set_password(self, password):
        """Hash and set user password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def accept_terms(self):
        """Mark terms and privacy policy as accepted."""
        self.terms_accepted = True
        self.privacy_accepted = True
        self.terms_accepted_at = datetime.utcnow()
    
    @property
    def is_active(self):
        """Check if account is active (computed from account_status)."""
        return self.is_account_active()
    
    @is_active.setter
    def is_active(self, value):
        """Set account status based on boolean value (for backward compatibility)."""
        # This is for backward compatibility - new code should use suspend_account/reactivate_account
        pass
    
    def is_account_active(self):
        """Check if account is active by looking at the latest AccountAction."""
        from app.models import AccountAction
        
        # Get the most recent account action
        latest_action = AccountAction.query.filter_by(user_id=self.id)\
            .order_by(AccountAction.created_at.desc()).first()
        
        if not latest_action:
            # No actions means account is active
            return True
        
        # Account is active if the latest action is 'reactivate'
        # Account is suspended if latest action is 'suspend' and suspension hasn't expired
        # Account is banned if latest action is 'ban'
        if latest_action.action_type == 'ban':
            return False
        elif latest_action.action_type == 'suspend':
            # Check if suspension has expired
            if latest_action.suspension_until and latest_action.suspension_until < datetime.utcnow():
                return True  # Suspension expired, account is active
            return False  # Still suspended
        elif latest_action.action_type == 'reactivate':
            return True
        
        return True  # Default to active
    
    def get_account_status(self):
        """Get current account status based on AccountAction history."""
        from app.models import AccountAction
        
        latest_action = AccountAction.query.filter_by(user_id=self.id)\
            .order_by(AccountAction.created_at.desc()).first()
        
        if not latest_action:
            return 'active'
        
        if latest_action.action_type == 'ban':
            return 'banned'
        elif latest_action.action_type == 'suspend':
            # Check if suspension expired
            if latest_action.suspension_until and latest_action.suspension_until < datetime.utcnow():
                return 'active'
            return 'suspended'
        elif latest_action.action_type == 'reactivate':
            return 'active'
        
        return 'active'
    
    def suspend_account(self, reason=None, suspension_until=None, suspended_by=None):
        """Suspend user account temporarily."""
        from app.models import AccountAction
        from app import db
        
        if not suspended_by:
            raise ValueError("suspended_by is required")
        
        # Create account action record
        action = AccountAction(
            user_id=self.id,
            action_type='suspend',
            reason=reason,
            suspension_until=suspension_until,
            performed_by_id=suspended_by.id if hasattr(suspended_by, 'id') else suspended_by
        )
        
        db.session.add(action)
        self.updated_at = datetime.utcnow()
    
    def ban_account(self, reason, banned_by):
        """Ban user account permanently."""
        from app.models import AccountAction
        from app import db
        
        if not banned_by:
            raise ValueError("banned_by is required")
        
        # Create account action record
        action = AccountAction(
            user_id=self.id,
            action_type='ban',
            reason=reason,
            performed_by_id=banned_by.id if hasattr(banned_by, 'id') else banned_by
        )
        
        db.session.add(action)
        self.updated_at = datetime.utcnow()
    
    def reactivate_account(self, reactivated_by=None):
        """Reactivate a suspended or banned account."""
        from app.models import AccountAction
        from app import db
        
        if reactivated_by:
            # Create account action record
            action = AccountAction(
                user_id=self.id,
                action_type='reactivate',
                performed_by_id=reactivated_by.id if hasattr(reactivated_by, 'id') else reactivated_by
            )
            db.session.add(action)
        
        self.updated_at = datetime.utcnow()
    
    def get_account_actions(self, limit=None):
        """Get account action history."""
        from app.models import AccountAction
        
        query = AccountAction.query.filter_by(user_id=self.id)\
            .order_by(AccountAction.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_account_status_display(self):
        """Get human-readable account status."""
        status = self.get_account_status()
        return status.title()
    
    def __repr__(self):
        return f'<User {self.full_name} ({self.role_type})>'


class Admin(User):
    """
    Administrator model with full system access.
    Can manage all accounts and system settings.
    """
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    admin_level = db.Column(db.String(50), default='super_admin')
    
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }


class Manager(User):
    """
    Manager model for managing rider and consumer accounts.
    Three types: Head Manager, Rider Manager, Consumer Manager.
    """
    __tablename__ = 'managers'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    manager_type = db.Column(db.String(50), nullable=False)  # head, rider, consumer
    
    # Relationships
    managed_riders = db.relationship('Rider', foreign_keys='Rider.manager_id', backref='manager', lazy='dynamic')
    managed_consumers = db.relationship('Consumer', foreign_keys='Consumer.manager_id', backref='manager', lazy='dynamic')
    
    __mapper_args__ = {
        'polymorphic_identity': 'manager',
    }
    
    def can_manage_riders(self):
        """Check if manager can manage rider accounts."""
        return self.manager_type in ['head', 'rider']
    
    def can_manage_consumers(self):
        """Check if manager can manage consumer accounts."""
        return self.manager_type in ['head', 'consumer']
    
    def can_manage_managers(self):
        """Check if manager can manage other managers."""
        return self.manager_type == 'head'


class Rider(User):
    """
    Rider/Driver model for delivery personnel.
    Can accept orders and deliver goods to consumers.
    """
    __tablename__ = 'riders'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'), nullable=True)
    
    # Rider-specific fields
    is_available = db.Column(db.Boolean, default=True)
    current_latitude = db.Column(db.Float)
    current_longitude = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)
    
    # Stats
    total_orders_completed = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    total_earnings = db.Column(db.Float, default=0.0)
    
    # Relationships
    vehicle = db.relationship('Vehicle', backref='rider', uselist=False, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='rider', lazy='dynamic') # Order history preserved unless consumer is deleted
    favorited_by = db.relationship('Consumer', secondary='consumer_favorites', back_populates='favorite_riders')
    
    __mapper_args__ = {
        'polymorphic_identity': 'rider',
    }
    
    def update_location(self, latitude, longitude):
        """Update rider's current location."""
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.last_location_update = datetime.utcnow()
    
    def update_rating(self, new_rating):
        """Update rider's average rating. Note: total_orders_completed is already incremented when order completes."""
        # Calculate new average rating without incrementing total_orders_completed again
        # since it was already incremented in orders.manage
        if self.total_orders_completed <= 1:
            self.average_rating = new_rating
        else:
            # We use total_orders_completed - 1 because it already includes the current order
            previous_total = self.average_rating * (self.total_orders_completed - 1)
            self.average_rating = (previous_total + new_rating) / self.total_orders_completed


class Consumer(User):
    """
    Consumer/User model for customers ordering deliveries.
    Can place orders and track deliveries.
    """
    __tablename__ = 'consumers'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'), nullable=True)
    
    # Consumer-specific fields
    default_address = db.Column(db.Text)
    
    # Stats
    total_orders_placed = db.Column(db.Integer, default=0)
    
    # Relationships
    orders = db.relationship('Order', backref='consumer', lazy='dynamic', cascade='all, delete-orphan')
    favorite_riders = db.relationship('Rider', secondary='consumer_favorites', back_populates='favorited_by')
    
    __mapper_args__ = {
        'polymorphic_identity': 'consumer',
    }
    
    def add_favorite_rider(self, rider):
        """Add a rider to favorites."""
        if rider not in self.favorite_riders:
            self.favorite_riders.append(rider)
    
    def remove_favorite_rider(self, rider):
        """Remove a rider from favorites."""
        if rider in self.favorite_riders:
            self.favorite_riders.remove(rider)


# Association table for consumer favorite riders
consumer_favorites = db.Table('consumer_favorites',
    db.Column('consumer_id', db.Integer, db.ForeignKey('consumers.id'), primary_key=True),
    db.Column('rider_id', db.Integer, db.ForeignKey('riders.id'), primary_key=True),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)
