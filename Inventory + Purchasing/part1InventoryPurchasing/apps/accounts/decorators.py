from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

def require_full_account(view_func):
    """
    Server-side decorator to block Guest users from executing sensitive
    write operations (updating org settings, deleting records, etc.).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if getattr(request, 'is_guest', False) or request.session.get('is_guest', False):
            messages.warning(
                request,
                "Action restricted in Guest Demo Mode. Please create a free account to enable full admin permissions."
            )
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def require_permission(role_required):
    """
    Server-side RBAC decorator to enforce minimum role authorization.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            profile = getattr(request, 'user_profile', None)
            if not profile:
                messages.error(request, "Permission denied. User profile missing.")
                return redirect('login')

            # Owner and Admin have all access
            if profile.role in ['OWNER', 'ADMIN']:
                return view_func(request, *args, **kwargs)

            if profile.role != role_required:
                messages.error(request, f"Permission denied. Required role: {role_required}.")
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
