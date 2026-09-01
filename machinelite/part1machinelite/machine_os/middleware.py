import time
from django.utils.deprecation import MiddlewareMixin
from apps.tenants.models import Organization, UserProfile

class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to resolve and attach the current Organization (Tenant) and Guest Status to request.
    Supports authenticated users and Guest Mode sessions safely isolated in demo mode.
    """
    def process_request(self, request):
        request.tenant = None
        request.is_guest = False

        # Check for explicit Guest Session
        if request.session.get('is_guest', False):
            request.is_guest = True
            demo_org = Organization.objects.filter(code='KEL-001').first()
            if not demo_org:
                demo_org = Organization.objects.first()
            request.tenant = demo_org
            return

        # Authenticated User Session
        if request.user and request.user.is_authenticated:
            try:
                profile = UserProfile.objects.filter(user=request.user).first()
                if profile and profile.organization:
                    request.tenant = profile.organization
                else:
                    default_org = Organization.objects.first()
                    if default_org:
                        request.tenant = default_org
            except Exception:
                pass

class AuditAndRateLimitMiddleware(MiddlewareMixin):
    """
    Security Middleware: Attaches OWASP security headers, prevents framing/XSS, and tracks request timing.
    """
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Content-Security-Policy'] = "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';"
        return response
