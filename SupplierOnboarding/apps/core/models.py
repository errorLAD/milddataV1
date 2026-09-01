import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='org_logos/', null=True, blank=True)
    domain = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        ADMIN = 'ADMIN', 'Admin'
        PROCUREMENT_MANAGER = 'PROCUREMENT_MANAGER', 'Procurement Manager'
        REVIEWER = 'REVIEWER', 'Reviewer'
        VIEWER = 'VIEWER', 'Viewer'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.PROCUREMENT_MANAGER)
    phone = models.CharField(max_length=50, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def is_admin_or_owner(self):
        return self.role in [self.Role.OWNER, self.Role.ADMIN] or self.is_superuser

class ActivityLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    action = models.CharField(max_length=255)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    object_name = models.CharField(max_length=255, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} on {self.object_name or self.object_type}"

class Notification(models.Model):
    class Type(models.TextChoices):
        EXPIRY = 'EXPIRY', 'Document Expiry'
        DOCUMENT = 'DOCUMENT', 'Document Activity'
        APPROVAL = 'APPROVAL', 'Approval Requirement'
        COMPLIANCE = 'COMPLIANCE', 'Compliance Alert'
        ONBOARDING = 'ONBOARDING', 'Onboarding Status'
        SYSTEM = 'SYSTEM', 'System Notification'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, null=True)
    notification_type = models.CharField(max_length=30, choices=Type.choices, default=Type.SYSTEM)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.organization.name}"
