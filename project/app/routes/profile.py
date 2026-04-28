"""
Profile management routes for ComeHere Rider (CHR).
Handles profile viewing, editing, and picture uploads.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from app import db, limiter
from app.models import User, Rider, Consumer, Document
from app.utils import save_file, delete_file, get_file_url
from app.utils.validators import validate_phone_number, validate_email, validate_address
from app.utils.password_validator import validate_password_form
import os
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/')
@login_required
def view():
    """View user profile."""
    return render_template('profile/view.html', user=current_user)


@profile_bp.route('/edit', methods=['GET'])
@login_required
def edit():
    """Show profile edit page."""
    return render_template('profile/edit.html', user=current_user)


@profile_bp.route('/update-info', methods=['POST'])
@login_required
def update_info():
    """Update profile information only."""
    # Get form data
    full_name = request.form.get('full_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    
    # Validate inputs
    if not full_name or len(full_name) < 3:
        flash('Full name must be at least 3 characters.', 'error')
        return redirect(url_for('profile.edit'))
    
    # Validate phone
    phone_valid, phone_result = validate_phone_number(phone_number)
    if not phone_valid:
        flash(phone_result, 'error')
        return redirect(url_for('profile.edit'))
    
    # Validate email if provided
    if email:
        email_valid, email_error = validate_email(email)
        if not email_valid:
            flash(email_error, 'error')
            return redirect(url_for('profile.edit'))
    
    # Validate address if provided
    if address:
        address_valid, address_error = validate_address(address)
        if not address_valid:
            flash(address_error, 'error')
            return redirect(url_for('profile.edit'))
    
    # Update user data
    current_user.full_name = full_name
    current_user.phone_number = phone_result
    current_user.email = email if email else None
    current_user.address = address if address else None
    
    try:
        db.session.commit()
        flash('Profile information updated successfully!', 'success')
        return redirect(url_for('profile.view'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {str(e)}', 'error')
        return redirect(url_for('profile.edit'))


@profile_bp.route('/update-picture', methods=['POST'])
@login_required
def update_picture():
    """Update profile picture only."""
    if 'profile_picture' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('profile.edit'))
    
    file = request.files['profile_picture']
    if not file or not file.filename:
        flash('No file selected.', 'error')
        return redirect(url_for('profile.edit'))
    
    # Delete old picture if exists
    if current_user.profile_picture:
        delete_file(current_user.profile_picture, 'profiles')
    
    # Save new picture
    success, result = save_file(file, 'profiles', 'image')
    if success:
        current_user.profile_picture = result
        try:
            db.session.commit()
            flash('Profile picture updated successfully!', 'success')
            return redirect(url_for('profile.view'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating picture: {str(e)}', 'error')
    else:
        flash(result, 'error')
    
    return redirect(url_for('profile.edit'))


@profile_bp.route('/delete-picture', methods=['POST'])
@login_required
def delete_picture():
    """Delete profile picture."""
    if current_user.profile_picture:
        delete_file(current_user.profile_picture, 'profiles')
        current_user.profile_picture = None
        try:
            db.session.commit()
            flash('Profile picture removed successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error removing picture: {str(e)}', 'error')
    else:
        flash('No profile picture to remove.', 'info')
    
    return redirect(url_for('profile.edit'))


@profile_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password with current password verification."""
    current_password = request.form.get('current_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    # Validate inputs
    if not current_password:
        flash('Current password is required.', 'error')
        return redirect(url_for('profile.edit'))
    
    if not new_password:
        flash('New password is required.', 'error')
        return redirect(url_for('profile.edit'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('profile.edit'))
    
    # Verify current password
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('profile.edit'))
    
    # Check if new password is different from current
    if current_user.check_password(new_password):
        flash('New password must be different from your current password.', 'error')
        return redirect(url_for('profile.edit'))
    
    # Validate new password strength
    validation_result = validate_password_form(new_password, confirm_password)
    if not validation_result['is_valid']:
        for error in validation_result['errors']:
            flash(error, 'error')
        return redirect(url_for('profile.edit'))
    
    # Update password
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('profile.view'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error changing password: {str(e)}', 'error')
        return redirect(url_for('profile.edit'))


@profile_bp.route('/documents')
@login_required
def documents():
    """View user documents."""
    user_documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    return render_template('profile/documents.html', documents=user_documents, document_types=Document.DOCUMENT_TYPES)


@profile_bp.route('/upload-document', methods=['POST'])
@login_required
def upload_document():
    """Upload a new document."""
    if 'document_file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('profile.documents'))
    
    file = request.files['document_file']
    document_type = request.form.get('document_type', '').strip()
    
    if not file or not file.filename:
        flash('No file selected.', 'error')
        return redirect(url_for('profile.documents'))
    
    if not document_type or document_type not in Document.DOCUMENT_TYPES:
        flash('Please select a valid document type.', 'error')
        return redirect(url_for('profile.documents'))
    
    # Validate file type
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp'}
    file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_extension not in allowed_extensions:
        flash('Invalid file type. Please upload PDF, JPG, PNG, GIF, or WebP files only.', 'error')
        return redirect(url_for('profile.documents'))
    
    # Save document file
    success, result = save_file(file, 'documents', 'document')
    if success:
        # Create document record
        document = Document(
            user_id=current_user.id,
            document_type=document_type,
            original_filename=secure_filename(file.filename),
            stored_filename=result,
            file_size=len(file.read()),
            mime_type=file.mimetype
        )
        
        try:
            db.session.add(document)
            db.session.commit()
            flash(f'{Document.DOCUMENT_TYPES[document_type]} uploaded successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            delete_file(result, 'documents')  # Clean up uploaded file
            flash(f'Error saving document: {str(e)}', 'error')
    else:
        flash(result, 'error')
    
    return redirect(url_for('profile.documents'))


@profile_bp.route('/download-document/<int:document_id>')
@login_required
def download_document(document_id):
    """Download a document."""
    document = Document.query.get_or_404(document_id)
    
    # Check if user owns the document or is authorized to view it
    if document.user_id != current_user.id:
        # Check if current user is a manager who can access this document
        if current_user.role_type not in ['manager', 'admin']:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('profile.documents'))
        
        # Additional manager authorization check would go here
        # For now, allow managers and admins to download any document
    
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', document.stored_filename)
        return send_file(
            file_path,
            as_attachment=True,
            download_name=document.original_filename,
            mimetype=document.mime_type
        )
    except FileNotFoundError:
        flash('Document file not found.', 'error')
        return redirect(url_for('profile.documents'))


@profile_bp.route('/delete-document/<int:document_id>', methods=['POST'])
@login_required
def delete_document(document_id):
    """Delete a document."""
    document = Document.query.get_or_404(document_id)
    
    # Check if user owns the document
    if document.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('profile.documents'))
    
    try:
        # Delete file from storage
        delete_file(document.stored_filename, 'documents')
        
        # Delete database record
        db.session.delete(document)
        db.session.commit()
        
        flash(f'{document.get_document_type_display()} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting document: {str(e)}', 'error')
    
    return redirect(url_for('profile.documents'))
