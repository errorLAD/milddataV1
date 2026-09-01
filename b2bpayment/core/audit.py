import logging
from core.models import SecurityAuditLog

logger = logging.getLogger('security_audit')

def get_client_ip(request):
    """Extract client IP address safely from request headers."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_security_event(event_type, request=None, user=None, username='', details=''):
    """
    Records a security audit log entry.
    Ensures sensitive fields like passwords, tokens, or card numbers are never logged.
    """
    try:
        ip_addr = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
        
        target_user = user or (request.user if request and hasattr(request, 'user') and request.user.is_authenticated else None)
        target_username = username or (target_user.username if target_user else '')

        # Scrub sensitive substrings if present in details
        sanitized_details = str(details)
        for sensitive_word in ['password', 'secret', 'token', 'card_number', 'cvv', 'upi_pin']:
            if sensitive_word in sanitized_details.lower():
                sanitized_details = f"[Sanitized details for {event_type}]"
                break

        SecurityAuditLog.objects.create(
            event_type=event_type,
            user=target_user,
            username=target_username,
            ip_address=ip_addr,
            user_agent=user_agent,
            details=sanitized_details[:1000]
        )
        logger.info(f"SECURITY_AUDIT: {event_type} | User: {target_username} | IP: {ip_addr}")
    except Exception as e:
        logger.error(f"Failed to log security audit event {event_type}: {e}")
