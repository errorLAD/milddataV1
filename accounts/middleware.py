import time
import logging
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)

# Guest session TTL: 2 hours (7200 seconds)
GUEST_SESSION_MAX_AGE = 7200


class GuestAccessMiddleware:
    """
    Middleware to manage guest sessions, handle auto-expiration,
    and strictly enforce server-side guest access restrictions.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, "session") and request.session.get("is_guest"):
            created_at = request.session.get("guest_created_at", 0)
            now = time.time()

            # Auto-expire stale guest sessions
            if created_at and (now - created_at) > GUEST_SESSION_MAX_AGE:
                request.session.flush()
                messages.info(request, "Your temporary guest session has expired. You may continue as guest or log in.")
                return redirect("home")

            path = request.path

            # Strictly enforce server-side restrictions on protected paths/methods
            restricted_paths = [
                "/admin/",
                "/products/payment/",
            ]
            
            is_restricted_path = any(path.startswith(rp) for rp in restricted_paths)
            is_purchase_attempt = path.startswith("/products/") and request.method == "POST" and "payment" not in path

            if is_restricted_path or is_purchase_attempt:
                messages.warning(
                    request,
                    "You are currently in Guest Mode. Please log in or sign up for a full account to purchase products or access account management.",
                )
                login_url = reverse("accounts:login")
                return redirect(f"{login_url}?next={path}")

        response = self.get_response(request)
        return response
