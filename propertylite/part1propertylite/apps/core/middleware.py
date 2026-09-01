from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from .models import GuestSession

class PropFlowSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Guest Session Expiration Check
        if request.user.is_authenticated and getattr(request.user, 'role', None) == 'GUEST':
            guest_session = GuestSession.objects.filter(guest_user=request.user).first()
            if guest_session and timezone.now() > guest_session.expires_at:
                logout(request)
                messages.warning(request, "Your temporary guest session has expired. Please sign in or start a new guest session.")
                return redirect('login')

        response = self.get_response(request)

        # 2. HTTP Security Headers Hardening
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Referrer-Policy'] = 'same-origin'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response
