"""
Account Action models for tracking user account status changes.
"""
from datetime import datetime
from app import db


class AccountAction(db.Model):
    """
    Model for tracking all user account status changes (suspend, ban, reactivate).
    Provides audit trail and history of account management actions.
    """
    __tablename__ = 'account_actions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.String(20), nullable=False)  # suspend, ban, reactivate
    reason = db.Column(db.Text, nullable=True)  # Reason for the action
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # For suspensions
    suspension_until = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='account_actions')
    performed_by = db.relationship('User', foreign_keys=[performed_by_id], backref='performed_actions')

    def __repr__(self):
        return f'<AccountAction {self.action_type} for User {self.user_id} by {self.performed_by_id}>'
