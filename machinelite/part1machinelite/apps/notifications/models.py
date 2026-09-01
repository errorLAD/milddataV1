from django.db import models
from django.contrib.auth.models import User
from apps.tenants.models import Organization

class Notification(models.Model):
    LEVEL_CHOICES = (
        ('info', 'Information'),
        ('warning', 'Warning Alert'),
        ('danger', 'Critical Alert'),
        ('success', 'Success Notice'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')
    link_url = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_level_display()}] {self.title} (Read: {self.is_read})"
