"""
File upload utilities for ComeHere Rider (CHR).
Handles secure file uploads for profile pictures and documents.
"""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

# Allowed extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf'}

def allowed_file(filename, file_type='image'):
    """
    Check if file extension is allowed.
    
    Args:
        filename: Name of the file
        file_type: Type of file ('image' or 'document')
    
    Returns:
        Boolean indicating if file is allowed
    """
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'document':
        return ext in ALLOWED_DOCUMENT_EXTENSIONS
    else:
        return False


def get_file_extension(filename):
    """Get file extension from filename."""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def generate_unique_filename(filename):
    """
    Generate a unique filename using UUID while preserving extension.
    
    Args:
        filename: Original filename
    
    Returns:
        Unique filename with UUID
    """
    ext = get_file_extension(filename)
    unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return secure_filename(unique_name)


def save_file(file, upload_folder, file_type='image'):
    """
    Save uploaded file securely.
    
    Args:
        file: FileStorage object from request.files
        upload_folder: Folder to save file (relative to UPLOAD_FOLDER)
        file_type: Type of file ('image' or 'document')
    
    Returns:
        Tuple (success: bool, filename/error: str)
    """
    if not file or file.filename == '':
        return False, 'No file selected'
    
    if not allowed_file(file.filename, file_type):
        allowed = ALLOWED_IMAGE_EXTENSIONS if file_type == 'image' else ALLOWED_DOCUMENT_EXTENSIONS
        return False, f'File type not allowed. Allowed: {", ".join(allowed)}'
    
    # Check file size (5MB for images, 10MB for documents)
    max_size = 5 * 1024 * 1024 if file_type == 'image' else 10 * 1024 * 1024
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > max_size:
        max_mb = 5 if file_type == 'image' else 10
        return False, f'File too large. Maximum size: {max_mb}MB'
    
    # Generate unique filename
    filename = generate_unique_filename(file.filename)
    
    # Create upload directory if it doesn't exist
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_folder)
    os.makedirs(upload_path, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_path, filename)
    try:
        file.save(filepath)
        return True, filename
    except Exception as e:
        current_app.logger.error(f'Error saving file: {str(e)}')
        return False, 'Error saving file'


def delete_file(filename, upload_folder):
    """
    Delete a file from upload folder.
    
    Args:
        filename: Name of file to delete
        upload_folder: Folder containing the file
    
    Returns:
        Boolean indicating success
    """
    if not filename:
        return False
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_folder, filename)
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception as e:
        current_app.logger.error(f'Error deleting file: {str(e)}')
        return False


def get_file_url(filename, upload_folder):
    """
    Get URL for uploaded file.
    
    Args:
        filename: Name of the file
        upload_folder: Folder containing the file
    
    Returns:
        URL string or None
    """
    if not filename:
        return None
    
    return f'/static/uploads/{upload_folder}/{filename}'
