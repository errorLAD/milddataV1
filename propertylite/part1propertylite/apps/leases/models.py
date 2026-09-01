from django.db import models
from apps.core.models import Organization, User
from apps.properties.models import Property, Unit
import datetime
from builtins import property as py_property

class Lease(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_EXPIRING_SOON = 'EXPIRING_SOON'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_TERMINATED = 'TERMINATED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_EXPIRING_SOON, 'Expiring Soon'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_TERMINATED, 'Terminated'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='leases')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='leases')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='leases')
    tenant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='leases',
        limit_choices_to={'role': User.ROLE_TENANT}
    )
    
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    rent_due_day = models.IntegerField(default=1) # 1st of month
    grace_period_days = models.IntegerField(default=5)
    late_fee_amount = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)
    rent_escalation_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    notice_period_days = models.IntegerField(default=30)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    lease_document = models.FileField(upload_to='lease_docs/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date']

    def __str__(self):
        return f"Lease #{self.id}: {self.tenant.get_full_name()} ({self.unit})"

    @py_property
    def is_expiring_within_30_days(self):
        if not self.end_date or self.status != self.STATUS_ACTIVE:
            return False
        today = datetime.date.today()
        days_left = (self.end_date - today).days
        return 0 <= days_left <= 30
