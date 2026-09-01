from django.db import models
from apps.tenants.models import Organization
from apps.machines.models import Machine

class RentalCustomer(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='rental_customers')
    name = models.CharField(max_length=150)
    company_name = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True, help_text="GST / VAT / Tax ID")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.company_name or 'Individual'})"

class RentalContract(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active Rental'),
        ('completed', 'Completed & Returned'),
        ('cancelled', 'Cancelled'),
    )

    RATE_TYPE_CHOICES = (
        ('daily', 'Daily Rental Rate'),
        ('hourly', 'Hourly Billed Rate'),
        ('monthly', 'Monthly Contract'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='rental_contracts')
    contract_number = models.CharField(max_length=50)
    customer = models.ForeignKey(RentalCustomer, on_delete=models.CASCADE, related_name='contracts')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='rental_contracts')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='daily')
    agreed_rate = models.DecimalField(max_digits=12, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    handover_meter = models.FloatField(help_text="Meter reading at handover time")
    return_meter = models.FloatField(null=True, blank=True, help_text="Meter reading upon return")
    handover_condition = models.TextField(blank=True, null=True, default="Passed 15-point inspection cleanly.")
    return_condition = models.TextField(blank=True, null=True)
    damage_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.contract_number} - {self.machine.name} ({self.customer.name})"
