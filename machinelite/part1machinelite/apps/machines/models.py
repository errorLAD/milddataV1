from django.db import models
from apps.tenants.models import Organization

class Machine(models.Model):
    CATEGORY_CHOICES = (
        ('jcb', 'JCB Backhoe Loader'),
        ('excavator', 'Excavator'),
        ('crane', 'Mobile Crane'),
        ('dumper', 'Dumper / Tipper'),
        ('loader', 'Wheel Loader'),
        ('tractor', 'Tractor'),
        ('generator', 'Diesel Generator'),
        ('truck', 'Heavy Duty Truck'),
        ('other', 'Other Heavy Equipment'),
    )

    STATUS_CHOICES = (
        ('working', 'Working / Active'),
        ('idle', 'Idle / Available'),
        ('maintenance', 'Scheduled Maintenance'),
        ('breakdown', 'Under Breakdown'),
        ('rented', 'On Client Rent'),
    )

    TRACKING_CHOICES = (
        ('hours', 'Engine Hours (HR)'),
        ('km', 'Odometer Kilometers (KM)'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='machines')
    name = models.CharField(max_length=150)
    reg_number = models.CharField(max_length=50)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='jcb')
    make_model = models.CharField(max_length=150)
    model_year = models.IntegerField(default=2022)
    tracking_type = models.CharField(max_length=20, choices=TRACKING_CHOICES, default='hours')
    current_meter = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='working')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=1200.00)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=9500.00)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=3500000.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['organization', 'reg_number']

    def __str__(self):
        return f"{self.name} ({self.reg_number})"

    @property
    def unit_label(self):
        return "HR" if self.tracking_type == 'hours' else "KM"

class MeterLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='meter_logs')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='meter_logs')
    date = models.DateField()
    meter_reading = models.FloatField()
    hours_worked = models.FloatField(default=0.0)
    recorded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-date', '-id']

class MachineLocation(models.Model):
    machine = models.OneToOneField(Machine, on_delete=models.CASCADE, related_name='location')
    latitude = models.FloatField(default=12.9716)
    longitude = models.FloatField(default=77.5946)
    location_name = models.CharField(max_length=255, default="NH-48 Expressway Site, Bengaluru")
    speed_kmh = models.FloatField(default=0.0)
    ignition_on = models.BooleanField(default=True)
    last_ping_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.machine.name} @ {self.location_name} ({self.latitude}, {self.longitude})"

class GeofenceZone(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='geofences')
    name = models.CharField(max_length=150)
    center_lat = models.FloatField(default=12.9716)
    center_lng = models.FloatField(default=77.5946)
    radius_km = models.FloatField(default=5.0)
    machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True, related_name='geofences')

    def __str__(self):
        return f"{self.name} ({self.radius_km} KM Radius)"

class LocationPing(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='location_pings')
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_name = models.CharField(max_length=255)
    speed_kmh = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
