from datetime import date
from django.db import models
from apps.tenants.models import Organization
from apps.machines.models import Machine
from apps.operators.models import Operator

class MachineDocument(models.Model):
    DOC_TYPE_CHOICES = (
        ('rc', 'Registration Certificate (RC)'),
        ('insurance', 'Commercial Insurance Policy'),
        ('fitness', 'Fitness Certificate'),
        ('permit', 'Road / Goods Permit'),
        ('puc', 'Pollution Control (PUC)'),
        ('license', 'Operator Heavy License'),
        ('other', 'Other Compliance Document'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='documents')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default='insurance')
    title = models.CharField(max_length=150)
    doc_number = models.CharField(max_length=100)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['expiry_date']

    def __str__(self):
        target = self.machine.name if self.machine else (self.operator.name if self.operator else "General")
        return f"{self.get_doc_type_display()} - {target} (Exp: {self.expiry_date})"

    @property
    def status_level(self):
        """Returns 'expired', 'warning' (due within 30 days), or 'valid'."""
        if not self.expiry_date:
            return 'valid'
        today = date.today()
        days_left = (self.expiry_date - today).days
        if days_left < 0:
            return 'expired'
        elif days_left <= 30:
            return 'warning'
        return 'valid'

    @property
    def days_remaining(self):
        if not self.expiry_date:
            return 999
        return (self.expiry_date - date.today()).days
