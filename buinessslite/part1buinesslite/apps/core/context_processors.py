from apps.core.models import Notification

def global_context(request):
    if hasattr(request, 'organization') and request.organization:
        org = request.organization
        notifications = Notification.objects.filter(organization=org)
        unread_count = notifications.filter(is_read=False).count()
        recent_notifs = notifications[:5]
        return {
            'organization': org,
            'user_profile': getattr(request, 'user_profile', None),
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifs,
            'currency_symbol': org.currency_symbol,
            'currency_code': org.currency_code,
        }
    return {
        'organization': None,
        'user_profile': getattr(request, 'user_profile', None),
        'unread_notifications_count': 0,
        'recent_notifications': [],
        'currency_symbol': '$',
        'currency_code': 'USD',
    }
