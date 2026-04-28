"""
Report model for ComeHere Rider (CHR).
Handles user reports, rider reports, and bug reports per plan.md.
"""
from datetime import datetime
from app import db


class Report(db.Model):
    """
    Report model for handling various types of reports.
    Types: user_report, rider_report, bug_report
    """
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Report type and status
    report_type = db.Column(db.String(50), nullable=False)  # user_report, rider_report, bug_report
    status = db.Column(db.String(50), default='pending')  # pending, investigating, resolved, dismissed
    
    # Reporter and reported user
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Null for bug reports
    
    # Report details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))  # harassment, order_issue, inappropriate_behavior, system_bug, etc.
    
    # Related order (if applicable)
    related_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    
    # Handler information
    handler_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Manager or Admin handling the report
    resolution_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # Relationships
    related_order = db.relationship('Order', backref='reports', foreign_keys=[related_order_id])
    handler = db.relationship('User', foreign_keys=[handler_id], backref='handled_reports')
    
    def assign_handler(self, handler_user):
        """Assign a manager or admin to handle the report."""
        self.handler_id = handler_user.id
        self.status = 'investigating'
    
    def resolve(self, resolution_notes):
        """Mark report as resolved with notes."""
        self.status = 'resolved'
        self.resolution_notes = resolution_notes
        self.resolved_at = datetime.utcnow()
    
    def dismiss(self, reason):
        """Dismiss report with reason."""
        self.status = 'dismissed'
        self.resolution_notes = reason
        self.resolved_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Report {self.report_type} - {self.status}>'
