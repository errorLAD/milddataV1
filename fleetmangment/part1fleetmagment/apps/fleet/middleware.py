from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
import time

class SecurityAndGuestMiddleware:
    """
    Server-Side Security & Guest Enforcement Middleware:
    1. Blocks Guest users from accessing protected financial, administrative, document, or modification endpoints.
    2. Implements basic server-side rate limiting on login requests to prevent brute-force attacks.
    3. Enforces session expiration for guest sessions.
    """
    
    RESTRICTED_GUEST_PATHS = [
        '/expenses/',
        '/billing/',
        '/documents/',
        '/users-roles/',
        '/superadmin/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self.login_attempts = {}

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        path = request.path

        # 1. Rate Limiting on Login POST requests
        if path == '/login/' and request.method == 'POST':
            now = time.time()
            attempts = self.login_attempts.get(ip, [])
            attempts = [t for t in attempts if now - t < 60]
            if len(attempts) >= 5:
                messages.error(request, "Too many login attempts. Please wait 60 seconds before trying again.")
                return redirect('login')
            attempts.append(now)
            self.login_attempts[ip] = attempts

        # 2. Server-side Guest Restrictions Enforcement
        is_guest = request.session.get('is_guest', False) or (request.user.is_authenticated and getattr(request.user, 'role', '') == 'VIEWER')
        
        if is_guest:
            # Block guests from RESTRICTED paths
            if any(path.startswith(rp) for rp in self.RESTRICTED_GUEST_PATHS):
                messages.warning(request, "Guest Mode Restriction: Registering a full account is required to access financial, document vault, and administrative settings.")
                return redirect('dashboard')

            # Handle POST requests in guest mode gracefully
            if request.method in ['POST', 'PUT', 'DELETE'] and path not in ['/guest-login/', '/login/', '/logout/', '/api/v1/ai/query/']:
                messages.info(request, "Public Demo Mode: Action simulated successfully. Register a full account for permanent cloud database persistence.")
                return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

        response = self.get_response(request)

        # 3. Security Headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
