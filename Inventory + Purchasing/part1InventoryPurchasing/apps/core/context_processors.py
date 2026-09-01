from apps.accounts.models import Organization
from apps.core.models import Notification

def organization_context(request):
    org = getattr(request, 'organization', None)
    profile = getattr(request, 'user_profile', None)

    if not org and request.user.is_authenticated:
        org = Organization.objects.first()

    unread_notifications_count = 0
    recent_notifications = []
    if org and request.user.is_authenticated:
        recent_notifications = Notification.objects.filter(organization=org)[:5]
        unread_notifications_count = Notification.objects.filter(organization=org, is_read=False).count()

    return {
        'org': org,
        'organization': org,
        'user_profile': profile,
        'unread_notifications_count': unread_notifications_count,
        'recent_notifications': recent_notifications,
    }
