import time
from django.shortcuts import redirect
from django.contrib import messages
from core.audit import log_security_event

GUEST_SESSION_MAX_AGE_SECONDS = 7200  # 2 Hours Expiry

# Paths allowed for guest users (GET requests)
GUEST_ALLOWED_GET_PATHS = [
    '/',
    '/landing/',
    '/accounts/login/',
    '/accounts/register/',
    '/accounts/guest-login/',
    '/accounts/upgrade-guest/',
    '/accounts/logout/',
    '/dashboard/',
    '/collections/',
    '/customers/',
    '/sales/',
    '/payments/',
    '/products/',
    '/suppliers/',
    '/promotions/',
    '/ai-advisor/',
    '/whatsapp/sandbox/',
    '/offline/',
]

# Restricted paths strictly forbidden for guests (even for GET)
GUEST_FORBIDDEN_PATHS = [
    '/platform-admin/',
    '/settings/',
    '/sales-agent/',
    '/whatsapp/send/',
]

class GuestAccessMiddleware:
    """
    Server-side enforcement of Guest Mode session lifecycle and feature restrictions.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Determine if current request is in guest session
        is_guest = request.session.get('is_guest', False)
        request.is_guest = is_guest

        if is_guest:
            # 1. Check guest session expiration
            created_at = request.session.get('guest_created_at')
            now = time.time()
            if created_at and (now - created_at > GUEST_SESSION_MAX_AGE_SECONDS):
                request.session.flush()
                messages.warning(request, "Your guest session has expired (2-hour limit). Please create a full account to continue.")
                log_security_event('LOGOUT', request, details="Guest session expired automatically")
                return redirect('accounts:login')

            path = request.path

            # Calculate remaining time in minutes
            remaining_seconds = max(0, GUEST_SESSION_MAX_AGE_SECONDS - int(now - (created_at or now)))
            request.guest_remaining_minutes = remaining_seconds // 60

            # 2. Block access to forbidden path prefixes for guests
            for forbidden_prefix in GUEST_FORBIDDEN_PATHS:
                if path.startswith(forbidden_prefix):
                    log_security_event('ACCESS_DENIED', request, details=f"Guest blocked from path: {path}")
                    messages.info(request, "Guest Mode Notice: Please register or upgrade to a full account to access this feature.")
                    return redirect('accounts:upgrade_guest')

            # 3. Enforce read-only restriction for guests on mutating POST/PUT/DELETE requests (except logout/upgrade)
            if request.method in ['POST', 'PUT', 'DELETE']:
                allowed_posts = ['/accounts/logout/', '/accounts/upgrade-guest/']
                if not any(path.startswith(p) for p in allowed_posts):
                    log_security_event('ACCESS_DENIED', request, details=f"Guest blocked from POST action: {path}")
                    messages.warning(request, "Guest Mode Notice: Action restricted in demo mode. Upgrade to a full account to make changes.")
                    return redirect('accounts:upgrade_guest')

        response = self.get_response(request)
        return response
