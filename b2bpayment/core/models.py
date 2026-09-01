from django.db import models

class TenantQuerySet(models.QuerySet):
    def for_business(self, business):
        if business:
            return self.filter(business=business)
        return self.none()

class TenantManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)

    def for_business(self, business):
        return self.get_queryset().for_business(business)

class TenantModel(models.Model):
    business = models.ForeignKey(
        'accounts.Business',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Business Tenant'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        abstract = True


class SecurityAuditLog(models.Model):
    EVENT_TYPES = (
        ('LOGIN_SUCCESS', 'Login Success'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('GUEST_LOGIN', 'Guest Login'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('ACCESS_DENIED', 'Access Denied'),
        ('SENSITIVE_ACTION', 'Sensitive Action'),
        ('GUEST_UPGRADE', 'Guest Upgraded'),
        ('FILE_UPLOAD_BLOCKED', 'File Upload Blocked'),
    )

    event_type = models.CharField(max_length=40, choices=EVENT_TYPES)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=150, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.event_type}] {self.username or 'Anonymous'} at {self.created_at}"

