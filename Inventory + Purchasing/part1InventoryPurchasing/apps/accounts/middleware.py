from apps.accounts.models import UserProfile, Organization
import time

class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.organization = None
        request.user_profile = None
        request.is_guest = False

        # Check guest session status
        if request.session.get('is_guest', False):
            expiry = request.session.get('guest_expiry', 0)
            if time.time() > expiry:
                # Guest session expired
                request.session.flush()
            else:
                request.is_guest = True

        if request.user.is_authenticated:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            request.user_profile = profile
            request.organization = profile.organization

            # If user has no organization yet and isn't on onboarding/login/logout page
            if not request.organization and not request.path.startswith('/accounts/'):
                org = Organization.objects.first()
                if org:
                    profile.organization = org
                    profile.save()
                    request.organization = org

        response = self.get_response(request)
        return response
