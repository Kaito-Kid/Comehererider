"""
Document models for ComeHere Rider (CHR).
Handles user document uploads and management.
"""
from datetime import datetime
from app import db


class Document(db.Model):
    """
    Document model for storing user-uploaded documents.
    Supports various document types with metadata.
    """
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Document details
    document_type = db.Column(db.String(50), nullable=False)  # birth_certificate, drivers_license, etc.
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    mime_type = db.Column(db.String(100))
    
    # Status and verification
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verification_notes = db.Column(db.Text)
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='documents')
    verifier = db.relationship('User', foreign_keys=[verified_by])
    
    # Document type constants
    DOCUMENT_TYPES = {
        'birth_certificate': 'Birth Certificate',
        'drivers_license': 'Driver\'s License',
        'school_id': 'School ID',
        'national_id': 'National ID',
        'passport': 'Passport',
        'voters_id': 'Voter\'s ID',
        'sss_id': 'SSS ID',
        'philhealth_id': 'PhilHealth ID',
        'tin_id': 'TIN ID',
        'postal_id': 'Postal ID',
        'prc_id': 'PRC ID',
        'senior_citizen_id': 'Senior Citizen ID',
        'pwd_id': 'PWD ID',
        'barangay_clearance': 'Barangay Clearance',
        'police_clearance': 'Police Clearance',
        'nbi_clearance': 'NBI Clearance',
        'medical_certificate': 'Medical Certificate',
        'other': 'Other Document'
    }
    
    def get_document_type_display(self):
        """Get human-readable document type."""
        return self.DOCUMENT_TYPES.get(self.document_type, self.document_type.title())
    
    def approve(self, verifier_id, notes=None):
        """Approve the document."""
        self.status = 'approved'
        self.verified_by = verifier_id
        self.verified_at = datetime.utcnow()
        if notes:
            self.verification_notes = notes
    
    def reject(self, verifier_id, notes):
        """Reject the document with notes."""
        self.status = 'rejected'
        self.verified_by = verifier_id
        self.verified_at = datetime.utcnow()
        self.verification_notes = notes
    
    def is_image(self):
        """Check if document is an image file."""
        image_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        return self.mime_type in image_types
    
    def is_pdf(self):
        """Check if document is a PDF file."""
        return self.mime_type == 'application/pdf'
    
    def get_file_size_display(self):
        """Get human-readable file size."""
        if not self.file_size:
            return 'Unknown'
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def __repr__(self):
        return f'<Document {self.original_filename} ({self.document_type})>'
