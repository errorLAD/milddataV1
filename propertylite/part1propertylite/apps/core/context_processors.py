from .models import Notification

def propflow_context(request):
    if not request.user.is_authenticated:
        return {}
    
    org = getattr(request.user, 'organization', None)
    unread_count = 0
    recent_notifs = []
    
    if org:
        notifs = Notification.objects.filter(recipient=request.user)
        unread_count = notifs.filter(is_read=False).count()
        recent_notifs = notifs[:5]
        
    return {
        'current_org': org,
        'user_role': getattr(request.user, 'role', 'TENANT'),
        'unread_notifications_count': unread_count,
        'recent_notifications': recent_notifs,
    }
