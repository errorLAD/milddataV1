from apps.core.models import UserProfile, Organization, UserRole

class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
            except UserProfile.DoesNotExist:
                # Auto-create profile and demo organization if missing
                org = Organization.objects.first()
                if not org:
                    org = Organization.objects.create(
                        name="Acme Global Trading",
                        country="United States",
                        currency_code="USD",
                        currency_symbol="$",
                        tax_name="Sales Tax",
                        tax_rate=10.00
                    )
                profile = UserProfile.objects.create(
                    user=request.user,
                    organization=org,
                    role=UserRole.OWNER
                )
            
            request.user_profile = profile
            request.organization = profile.organization
        else:
            request.user_profile = None
            request.organization = None

        response = self.get_response(request)
        return response
