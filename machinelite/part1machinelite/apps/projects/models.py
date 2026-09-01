from django.db import models
from apps.tenants.models import Organization
from apps.machines.models import Machine
from apps.operators.models import Operator

class Project(models.Model):
    STATUS_CHOICES = (
        ('ongoing', 'Ongoing Site'),
        ('upcoming', 'Upcoming Job'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=150)
    client_name = models.CharField(max_length=150)
    location = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=14, decimal_places=2, default=500000.00)

    class Meta:
        ordering = ['-start_date', 'name']

    def __str__(self):
        return f"{self.name} - {self.client_name}"

class MachineAllocation(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='allocations')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='allocations')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='allocations')
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True, related_name='allocations')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    agreed_rate = models.DecimalField(max_digits=12, decimal_places=2, default=1200.00, help_text="Hourly or daily billing rate")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.machine.name} assigned to {self.project.name}"
