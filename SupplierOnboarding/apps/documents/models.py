import uuid
from django.db import models
from apps.core.models import Organization, User
from apps.suppliers.models import Supplier, DocumentType

class SupplierDocument(models.Model):
    class Status(models.TextChoices):
        VERIFIED = 'VERIFIED', 'Verified'
        PENDING_REVIEW = 'PENDING_REVIEW', 'Pending Review'
        MISSING = 'MISSING', 'Missing'
        EXPIRING_SOON = 'EXPIRING_SOON', 'Expiring Soon'
        EXPIRED = 'EXPIRED', 'Expired'
        REJECTED = 'REJECTED', 'Rejected'

    class AIStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending AI Analysis'
        EXTRACTED = 'EXTRACTED', 'Extracted'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='documents')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, related_name='supplier_documents')
    
    file = models.FileField(upload_to='supplier_docs/', null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.IntegerField(default=0)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.MISSING)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    rejection_reason = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    ai_extracted_data = models.JSONField(default=dict, blank=True)
    ai_confidence = models.FloatField(default=0.0)
    ai_status = models.CharField(max_length=30, choices=AIStatus.choices, default=AIStatus.PENDING)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.document_type.name} - {self.supplier.legal_name}"
