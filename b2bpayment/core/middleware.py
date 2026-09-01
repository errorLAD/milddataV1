from accounts.models import Business

class TenantMiddleware:
    """
    Middleware that sets request.business based on the logged-in user's UserProfile or Guest session.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.business = None
        
        if request.user.is_authenticated:
            if hasattr(request.user, 'profile') and request.user.profile.business:
                request.business = request.user.profile.business
        elif request.session.get('is_guest'):
            # Guest mode: assign demo business context
            guest_b, _ = Business.objects.get_or_create(
                name="Demo Guest Business",
                defaults={
                    'owner_name': 'Guest User',
                    'phone': '9999999999',
                    'email': 'guest@demo.local',
                    'address': 'Demo Sandbox Location',
                    'is_active': True
                }
            )
            request.business = guest_b

        response = self.get_response(request)
        return response

