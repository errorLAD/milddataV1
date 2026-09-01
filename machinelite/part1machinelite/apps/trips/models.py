from django.db import models
from apps.tenants.models import Organization
from apps.machines.models import Machine
from apps.operators.models import Operator
from apps.projects.models import Project

class Trip(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('en_route', 'En Route / Transit'),
        ('in_progress', 'Work In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='trips')
    trip_number = models.CharField(max_length=50)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='trips')
    driver = models.ForeignKey(Operator, on_delete=models.CASCADE, related_name='trips')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='trips')
    pickup_location = models.CharField(max_length=200)
    drop_location = models.CharField(max_length=200)
    distance_km = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    proof_of_work = models.TextField(blank=True, null=True, help_text="Inspection notes & completion signoff")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.trip_number} - {self.machine.name} ({self.get_status_display()})"
