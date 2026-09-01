from django.db import models
from apps.core.models import Organization, User

class TenantProfile(models.Model):
    KYC_PENDING = 'PENDING'
    KYC_VERIFIED = 'VERIFIED'
    KYC_REJECTED = 'REJECTED'
    
    KYC_STATUS_CHOICES = [
        (KYC_PENDING, 'Pending Review'),
        (KYC_VERIFIED, 'Verified'),
        (KYC_REJECTED, 'Rejected'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='tenant_profiles')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant_profile')
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default=KYC_VERIFIED)
    id_document = models.FileField(upload_to='tenant_docs/', null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tenant: {self.user.get_full_name() or self.user.username}"
