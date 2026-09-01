from django.db import models
from apps.tenants.models import Organization
from apps.machines.models import Machine

class MaintenanceLog(models.Model):
    SERVICE_TYPE_CHOICES = (
        ('preventive', 'Preventive Service (Periodic)'),
        ('breakdown', 'Breakdown Repair'),
        ('hydraulic', 'Hydraulic System Service'),
        ('engine', 'Engine & Transmission Overhaul'),
        ('tire_track', 'Tires / Tracks Service'),
        ('inspection', 'General Inspection / Greasing'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='maintenance_logs')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='maintenance_logs')
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPE_CHOICES, default='preventive')
    date = models.DateField()
    meter_reading = models.FloatField(help_text="Meter reading when service took place")
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    vendor_mechanic = models.CharField(max_length=150, blank=True, null=True, help_text="Workshop or mechanic name")
    parts_replaced = models.TextField(blank=True, null=True, help_text="e.g. Engine oil filter, hydraulic seal kit")
    description = models.TextField(blank=True, null=True)
    next_service_meter = models.FloatField(null=True, blank=True, help_text="Target meter reading for next service")
    is_breakdown = models.BooleanField(default=False)
    downtime_hours = models.FloatField(default=0.0, help_text="Equipment downtime in hours")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.machine.name} - {self.get_service_type_display()} on {self.date}"
