from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import datetime
import uuid

class Organization(models.Model):
    PLAN_STARTER = 'STARTER'
    PLAN_PROFESSIONAL = 'PROFESSIONAL'
    PLAN_BUSINESS = 'BUSINESS'
    
    PLAN_CHOICES = [
        (PLAN_STARTER, 'Starter'),
        (PLAN_PROFESSIONAL, 'Professional'),
        (PLAN_BUSINESS, 'Business'),
    ]

    CURRENCY_CHOICES = [
        ('USD', '$ - US Dollar'),
        ('EUR', '€ - Euro'),
        ('GBP', '£ - British Pound'),
        ('INR', '₹ - Indian Rupee'),
        ('CAD', 'C$ - Canadian Dollar'),
        ('AUD', 'A$ - Australian Dollar'),
        ('AED', 'AED - UAE Dirham'),
        ('SAR', 'SAR - Saudi Riyal'),
        ('JPY', '¥ - Japanese Yen'),
        ('SGD', 'S$ - Singapore Dollar'),
    ]
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='org_logos/', null=True, blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_PROFESSIONAL)
    currency_code = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD')
    currency_symbol = models.CharField(max_length=10, default='$')
    is_active = models.BooleanField(default=True)
    is_demo_org = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    ROLE_SUPER_ADMIN = 'SUPER_ADMIN'
    ROLE_PROPERTY_MANAGER = 'PROPERTY_MANAGER'
    ROLE_PROPERTY_OWNER = 'PROPERTY_OWNER'
    ROLE_ACCOUNTANT = 'ACCOUNTANT'
    ROLE_MAINTENANCE_STAFF = 'MAINTENANCE_STAFF'
    ROLE_TENANT = 'TENANT'
    ROLE_GUEST = 'GUEST'
    
    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin'),
        (ROLE_PROPERTY_MANAGER, 'Property Manager'),
        (ROLE_PROPERTY_OWNER, 'Property Owner'),
        (ROLE_ACCOUNTANT, 'Accountant'),
        (ROLE_MAINTENANCE_STAFF, 'Maintenance Staff'),
        (ROLE_TENANT, 'Tenant'),
        (ROLE_GUEST, 'Guest Mode User'),
    ]
    
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='users', 
        null=True, 
        blank=True
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_PROPERTY_MANAGER)
    phone = models.CharField(max_length=30, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_guest(self):
        return self.role == self.ROLE_GUEST

    @property
    def is_tenant_user(self):
        return self.role == self.ROLE_TENANT

    @property
    def is_owner_user(self):
        return self.role == self.ROLE_PROPERTY_OWNER

class GuestSession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    guest_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guest_session')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"GuestSession {self.session_id} for {self.guest_user.username}"

class AuditLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"

class Notification(models.Model):
    TYPE_RENT_DUE = 'RENT_DUE'
    TYPE_PAYMENT = 'PAYMENT'
    TYPE_LEASE = 'LEASE'
    TYPE_MAINTENANCE = 'MAINTENANCE'
    TYPE_ANNOUNCEMENT = 'ANNOUNCEMENT'
    TYPE_SYSTEM = 'SYSTEM'
    
    TYPE_CHOICES = [
        (TYPE_RENT_DUE, 'Rent Due'),
        (TYPE_PAYMENT, 'Payment Received'),
        (TYPE_LEASE, 'Lease Update'),
        (TYPE_MAINTENANCE, 'Maintenance Request'),
        (TYPE_ANNOUNCEMENT, 'Announcement'),
        (TYPE_SYSTEM, 'System Alert'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_SYSTEM)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} -> {self.recipient.username}"
