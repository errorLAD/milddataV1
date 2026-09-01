from django.db import models
from django.contrib.auth.models import User

class Business(models.Model):
    name = models.CharField(max_length=255, verbose_name="Business Name")
    owner_name = models.CharField(max_length=255, verbose_name="Owner Full Name")
    phone = models.CharField(max_length=20, verbose_name="Business Phone Number")
    email = models.EmailField(blank=True, null=True, verbose_name="Business Email")
    address = models.TextField(blank=True, verbose_name="Business Address")
    gstin = models.CharField(max_length=20, blank=True, null=True, verbose_name="GSTIN Number")
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Businesses"

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('Owner', 'Owner'),
        ('Manager', 'Manager'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Owner')
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.business.name})"
