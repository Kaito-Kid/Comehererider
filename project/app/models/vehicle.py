"""
Vehicle model for ComeHere Rider (CHR).
Stores vehicle information for riders.
"""
from datetime import datetime
from app import db


class Vehicle(db.Model):
    """
    Vehicle model for rider vehicles.
    Each rider has one vehicle associated with their account.
    """
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('riders.id'), nullable=False, unique=True)
    
    # Vehicle details
    vehicle_name = db.Column(db.String(100), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)  # Tricycle, Motorcycle, etc.
    plate_number = db.Column(db.String(50), nullable=False, unique=True)
    
    # Additional info
    color = db.Column(db.String(50))
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Vehicle {self.vehicle_type} - {self.plate_number}>'
