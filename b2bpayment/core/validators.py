import os
import uuid
from django.core.exceptions import ValidationError
from core.audit import log_security_event

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.csv', '.xlsx'}
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'application/pdf',
    'text/csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_file_upload(file_obj, request=None):
    """
    Validates an uploaded file's extension, size, and MIME content.
    Raises ValidationError if invalid.
    """
    if not file_obj:
        return file_obj

    # 1. Check size limit
    if file_obj.size > MAX_FILE_SIZE_BYTES:
        if request:
            log_security_event('FILE_UPLOAD_BLOCKED', request, details=f"File too large: {file_obj.size} bytes")
        raise ValidationError(f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.")

    # 2. Check extension
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        if request:
            log_security_event('FILE_UPLOAD_BLOCKED', request, details=f"Disallowed extension: {ext}")
        raise ValidationError(f"File type '{ext}' is not allowed. Permitted types: {', '.join(ALLOWED_EXTENSIONS)}")

    # 3. Check content type header
    content_type = getattr(file_obj, 'content_type', '').lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        # Fallback check for images/pdfs
        if not (content_type.startswith('image/') or content_type == 'application/pdf' or 'csv' in content_type):
            if request:
                log_security_event('FILE_UPLOAD_BLOCKED', request, details=f"Disallowed MIME type: {content_type}")
            raise ValidationError("File content type validation failed.")

    return file_obj


def generate_safe_filename(instance, filename):
    """
    Generates a secure, unguessable filename to prevent path traversal and execution attacks.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = '.bin'
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('uploads', safe_name)
