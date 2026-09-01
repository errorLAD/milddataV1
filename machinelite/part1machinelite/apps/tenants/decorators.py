from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def guest_restricted(view_func):
    """
    Decorator to restrict guest users from performing mutation actions (creates, updates, deletes, uploads).
    If a guest attempts a restricted action, they are shown a friendly message and redirected to the upgrade page.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        is_guest = getattr(request, 'is_guest', False)
        if is_guest or not request.user.is_authenticated:
            messages.warning(
                request,
                "🔒 Guest Mode: Creating or modifying records is disabled in Demo Mode. Please sign in or upgrade to a full account."
            )
            return redirect('upgrade_account')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
