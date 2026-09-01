import os
import uuid
from functools import wraps
from django.http import HttpResponseForbidden, JsonResponse
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import redirect
from django.core.cache import cache

# Allowed File Extensions & MIME types
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
ALLOWED_MIME_TYPES = {'application/pdf', 'image/jpeg', 'image/png', 'image/pjpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_file_upload(file_obj):
    """
    Validates file upload extension, MIME type, file size, and generates a safe filename.
    """
    if not file_obj:
        raise ValidationError("No file uploaded.")

    # 1. Size Check
    if file_obj.size > MAX_FILE_SIZE:
        raise ValidationError(f"File size exceeds limit of 10 MB. Current size: {round(file_obj.size / (1024*1024), 2)} MB.")

    # 2. Extension Check
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Invalid file extension '{ext}'. Allowed extensions: PDF, JPG, PNG.")

    # 3. Content Type / MIME Check
    content_type = getattr(file_obj, 'content_type', '').lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"Invalid file type '{content_type}'. Must be a valid PDF, JPG, or PNG document.")

    # 4. Generate Safe Sanitized Filename
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_obj.name = safe_filename
    return safe_filename


def guest_forbidden(view_func):
    """
    Decorator enforcing that Guest users cannot access modifying or protected routes server-side.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        is_guest = request.session.get('is_guest', False) or (request.user.is_authenticated and getattr(request.user, 'role', '') == 'GUEST')
        if is_guest and request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            messages.error(request, "Guest Mode is read-only. Please register or login to perform this action.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def role_required(*allowed_roles):
    """
    Decorator to enforce Role-Based Access Control (RBAC) server-side.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            user_role = getattr(request.user, 'role', None)
            if user_role not in allowed_roles and not request.user.is_superuser:
                messages.error(request, "Access Denied: You do not have permission to access this resource.")
                return HttpResponseForbidden("403 Forbidden: Insufficient Permissions.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class SecurityHeadersMiddleware:
    """
    Injects enterprise HTTP Security Headers into all responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Content-Security-Policy'] = "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';"
        return response


class RateLimitMiddleware:
    """
    Simple IP & Session rate limiting middleware to prevent brute-force attacks.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in ['/login/', '/register/', '/portal/guest-login/'] and request.method == 'POST':
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
            cache_key = f"rate_limit_login_{ip}"
            attempts = cache.get(cache_key, 0)
            if attempts >= 10:
                messages.error(request, "Too many failed attempts. Please wait 1 minute before trying again.")
                return HttpResponseForbidden("429 Too Many Requests: Rate limit exceeded.")
            cache.set(cache_key, attempts + 1, timeout=60)
        return self.get_response(request)
