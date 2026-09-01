import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    High-level security middleware enforcing security response headers
    such as X-Content-Type-Options, X-Frame-Options, Referrer-Policy, and CSP.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Enforce security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # CSP (Content Security Policy) allowing self resources, Google Fonts, Razorpay, and PostImage logo
        csp_directives = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://checkout.razorpay.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https://i.postimg.cc https://*.razorpay.com; "
            "connect-src 'self' https://lumberjack.razorpay.com; "
            "frame-src 'self' https://api.razorpay.com;"
        )
        response["Content-Security-Policy"] = csp_directives

        return response
