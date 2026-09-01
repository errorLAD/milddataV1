from django.db import models
from apps.tenants.models import Organization

class Subscription(models.Model):
    TIER_CHOICES = (
        ('starter', 'Starter Plan (Up to 5 Machines)'),
        ('pro', 'Pro Fleet Plan (Up to 25 Machines)'),
        ('enterprise', 'Enterprise Unlimited Plan'),
    )

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='subscription')
    plan_tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='pro')
    machine_limit = models.IntegerField(default=25)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=4999.00)
    is_active = models.BooleanField(default=True)
    valid_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organization.name} - {self.get_plan_tier_display()}"
