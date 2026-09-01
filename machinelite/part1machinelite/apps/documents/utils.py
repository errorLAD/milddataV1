import os
import uuid
from django.core.exceptions import ValidationError

ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
ALLOWED_MIME_TYPES = {'application/pdf', 'image/jpeg', 'image/png', 'image/pjpeg'}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

def validate_uploaded_file(file_obj):
    """
    Validates uploaded document file extension, size, and content.
    Prevents executable or malicious file uploads.
    """
    if not file_obj:
        return True

    # 1. Size Check
    if file_obj.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File size exceeds maximum allowed ceiling of 5 MB (File size: {file_obj.size / (1024*1024):.1f} MB).")

    # 2. Extension Check
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Invalid file extension '{ext}'. Only .pdf, .jpg, .jpeg, and .png files are accepted.")

    # 3. Content Type Check
    content_type = getattr(file_obj, 'content_type', '').lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"Invalid MIME type '{content_type}'. Security policy rejects non-document files.")

    return True

def generate_safe_filename(original_filename):
    """
    Generates a secure UUID filename to prevent path traversal and execution attacks.
    """
    ext = os.path.splitext(original_filename)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"
