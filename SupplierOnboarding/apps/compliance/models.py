import uuid
from django.db import models
from apps.core.models import Organization, User
from apps.suppliers.models import Supplier
from apps.documents.models import SupplierDocument

class ComplianceIssue(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = 'CRITICAL', 'Critical'
        HIGH = 'HIGH', 'High'
        MEDIUM = 'MEDIUM', 'Medium'
        LOW = 'LOW', 'Low'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='compliance_issues')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='compliance_issues')
    document = models.ForeignKey(SupplierDocument, on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_issues')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    
    due_date = models.DateField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_compliance_issues')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity}] {self.title} - {self.supplier.legal_name}"
