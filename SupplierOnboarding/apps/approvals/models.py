import uuid
from django.db import models
from apps.core.models import Organization, User
from apps.suppliers.models import Supplier

class ApprovalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CHANGES_REQUESTED = 'CHANGES_REQUESTED', 'Changes Requested'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='approval_requests')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='approval_requests')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_assigned')
    
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    comments = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    risk_flags = models.JSONField(default=list, blank=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Approval for {self.supplier.legal_name} ({self.status})"
