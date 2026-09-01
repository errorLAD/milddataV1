import time
from django.utils import timezone

class GuestSessionMiddleware:
    """
    Manages temporary Guest Access sessions and auto-expiry.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_guest = request.session.get('is_guest', False)
        guest_created_at = request.session.get('guest_created_at', 0)

        if is_guest:
            # Check 1-hour auto expiry for guest sessions
            if time.time() - guest_created_at > 3600:  # 1 Hour timeout
                request.session.flush()
                request.is_guest = False
            else:
                request.is_guest = True
        else:
            request.is_guest = False

        return self.get_response(request)
