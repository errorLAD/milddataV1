from django.db import models
from apps.tenants.models import Organization
from apps.machines.models import Machine

class Operator(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active / On Duty'),
        ('on_leave', 'On Leave'),
        ('inactive', 'Inactive'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='operators')
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    license_number = models.CharField(max_length=100)
    license_expiry = models.DateField(null=True, blank=True)
    assigned_machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True, related_name='operators')
    daily_salary = models.DecimalField(max_digits=10, decimal_places=2, default=800.00)
    performance_score = models.IntegerField(default=92, help_text="Operator rating 0-100")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    joining_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.license_number})"

class OperatorAttendance(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='attendances')
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=(('present', 'Present'), ('absent', 'Absent'), ('leave', 'On Leave')), default='present')
    hours_worked = models.FloatField(default=8.0)
    overtime_hours = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-date']

class OperatorIncident(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='incidents')
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, related_name='incidents')
    machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    title = models.CharField(max_length=150)
    severity = models.CharField(max_length=20, choices=(('low', 'Minor'), ('medium', 'Moderate'), ('high', 'Severe Damage')), default='low')
    description = models.TextField()

    class Meta:
        ordering = ['-date']
