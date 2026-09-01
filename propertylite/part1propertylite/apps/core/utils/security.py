from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
import os
import re

ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.csv', '.xlsx'}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024 # 5 MB limit

def validate_uploaded_file(uploaded_file):
    """
    Server-side validation for file uploads:
    - Max size limit (5MB)
    - Extension whitelist check
    - Filename sanitization against path traversal
    """
    if not uploaded_file:
        return True

    if uploaded_file.size > MAX_UPLOAD_SIZE:
        raise ValidationError("File size exceeds maximum limit of 5 MB.")

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File type '{ext}' is not permitted.")

    # Sanitize filename (alphanumeric, underscores, hyphens)
    safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', uploaded_file.name)
    uploaded_file.name = safe_name
    return True

def guest_restricted(view_func):
    """
    Decorator enforcing Guest Access Restrictions server-side.
    If a guest attempts a modifying or sensitive operation, execution is blocked
    and the guest is prompted to upgrade to a full account.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and getattr(request.user, 'role', None) == 'GUEST':
            messages.warning(request, "🔒 Guest Access Mode: This action requires a full property manager account. Upgrade below to unlock full access.")
            return redirect('guest_upgrade')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
