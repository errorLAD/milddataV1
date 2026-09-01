import time
from collections import defaultdict
from django.http import HttpResponse
from django.shortcuts import render
from core.audit import get_client_ip, log_security_event

# In-memory rate limiting stores (IP -> list of timestamps)
_login_attempts = defaultdict(list)
_api_requests = defaultdict(list)

MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300  # 5 minutes

MAX_API_REQUESTS = 60
API_WINDOW_SECONDS = 60  # 1 minute


def is_rate_limited(ip_address, action_type='login'):
    now = time.time()
    if action_type == 'login':
        attempts = _login_attempts[ip_address]
        # Keep only timestamps within window
        valid_attempts = [t for t in attempts if now - t < LOGIN_WINDOW_SECONDS]
        _login_attempts[ip_address] = valid_attempts
        return len(valid_attempts) >= MAX_LOGIN_ATTEMPTS
    else:
        requests = _api_requests[ip_address]
        valid_requests = [t for t in requests if now - t < API_WINDOW_SECONDS]
        _api_requests[ip_address] = valid_requests
        return len(valid_requests) >= MAX_API_REQUESTS


def record_attempt(ip_address, action_type='login'):
    now = time.time()
    if action_type == 'login':
        _login_attempts[ip_address].append(now)
    else:
        _api_requests[ip_address].append(now)


class RateLimitMiddleware:
    """
    Middleware that enforces request rate limits on sensitive authentication and API routes.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.lower()
        ip = get_client_ip(request)

        # Check authentication / login rate limits
        if request.method == 'POST' and ('/accounts/login' in path or '/accounts/register' in path):
            if is_rate_limited(ip, 'login'):
                log_security_event('ACCESS_DENIED', request, details=f"Rate limit exceeded on {path}")
                return render(request, 'blocked.html', {
                    'title': 'Too Many Requests',
                    'message': 'Too many login attempts detected. Please wait 5 minutes before trying again.'
                }, status=429)

        # Check API rate limits
        if path.startswith('/api/'):
            if is_rate_limited(ip, 'api'):
                log_security_event('ACCESS_DENIED', request, details=f"API rate limit exceeded on {path}")
                return HttpResponse('{"error": "Too many requests. Please slow down."}', content_type='application/json', status=429)
            record_attempt(ip, 'api')

        return self.get_response(request)
