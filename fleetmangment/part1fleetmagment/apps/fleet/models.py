from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import math
import json

class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    max_vehicles = models.IntegerField(default=50)
    max_users = models.IntegerField(default=20)
    plan_name = models.CharField(max_length=50, default='PRO')
    is_active = models.BooleanField(default=True)
    
    # Country & Currency Preferences
    country_code = models.CharField(max_length=10, default='US')
    country_name = models.CharField(max_length=50, default='United States')
    currency_code = models.CharField(max_length=10, default='USD')
    currency_symbol = models.CharField(max_length=10, default='$')

    def __str__(self):
        return self.name



class User(AbstractUser):
    ROLE_CHOICES = (
        ('OWNER', 'Owner'),
        ('ADMIN', 'Admin'),
        ('FLEET_MANAGER', 'Fleet Manager'),
        ('DISPATCHER', 'Dispatcher'),
        ('ACCOUNTANT', 'Accountant'),
        ('MAINTENANCE_MANAGER', 'Maintenance Manager'),
        ('DRIVER', 'Driver / Operator'),
        ('VIEWER', 'Viewer'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='FLEET_MANAGER')
    phone = models.CharField(max_length=20, blank=True, null=True)
    photo = models.ImageField(upload_to='drivers/', blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    license_expiry = models.DateField(blank=True, null=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    driving_score = models.IntegerField(default=92)
    is_driver_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class Vehicle(models.Model):
    TYPE_CHOICES = (
        ('TRUCK', 'Truck'),
        ('VAN', 'Delivery Van'),
        ('CAR', 'Car'),
        ('BUS', 'Bus'),
        ('MOTORCYCLE', 'Motorcycle'),
        ('JCB', 'JCB Backhoe Loader'),
        ('EXCAVATOR', 'Excavator'),
        ('TRACTOR', 'Tractor'),
        ('LOADER', 'Wheel Loader'),
        ('GENERATOR', 'Diesel Generator'),
        ('OTHER', 'Other Heavy Equipment'),
    )
    STATUS_CHOICES = (
        ('MOVING', 'Moving'),
        ('IDLE', 'Idle'),
        ('STOPPED', 'Stopped'),
        ('OFFLINE', 'Offline'),
        ('MAINTENANCE', 'Under Maintenance'),
    )
    FUEL_CHOICES = (
        ('DIESEL', 'Diesel'),
        ('PETROL', 'Petrol'),
        ('ELECTRIC', 'Electric'),
        ('HYBRID', 'Hybrid'),
        ('CNG', 'CNG'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_code = models.CharField(max_length=50, help_text="Internal ID like TR-101 or JCB-04")
    registration_number = models.CharField(max_length=50)
    vehicle_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='TRUCK')
    brand = models.CharField(max_length=100, blank=True, default='')
    model = models.CharField(max_length=100, blank=True, default='')
    year = models.IntegerField(default=2023)
    vin = models.CharField(max_length=100, blank=True, default='')
    engine_number = models.CharField(max_length=100, blank=True, default='')
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='DIESEL')
    
    mileage_km = models.FloatField(default=0.0, help_text="Total Odometer (km)")
    engine_hours = models.FloatField(default=0.0, help_text="Total Engine Running Hours")
    purchase_date = models.DateField(null=True, blank=True)
    
    current_driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_vehicles')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='STOPPED')
    
    # Real-time Telemetry state
    last_lat = models.FloatField(null=True, blank=True)
    last_lng = models.FloatField(null=True, blank=True)
    last_speed = models.FloatField(default=0.0) # km/h
    last_heading = models.FloatField(default=0.0) # degrees
    last_gps_update = models.DateTimeField(null=True, blank=True)
    battery_level = models.IntegerField(default=95) # %
    signal_strength = models.IntegerField(default=4) # bars (1-5)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle_code} - {self.registration_number} ({self.get_vehicle_type_display()})"

    @property
    def is_stale_gps(self):
        if not self.last_gps_update:
            return True
        seconds = (timezone.now() - self.last_gps_update).total_seconds()
        return seconds > 600  # > 10 mins

    @property
    def health_score_breakdown(self):
        score = 100
        deductions = []
        
        # Check maintenance
        overdue_maint = self.maintenance_records.filter(status__in=['SCHEDULED', 'IN_PROGRESS'], next_due_date__lt=timezone.now().date()).count()
        if overdue_maint > 0:
            ded = overdue_maint * 10
            score -= ded
            deductions.append(f"-{ded} for {overdue_maint} overdue service schedule(s)")
            
        # Check expired documents
        expired_docs = self.documents.filter(expiry_date__lt=timezone.now().date()).count()
        if expired_docs > 0:
            ded = expired_docs * 8
            score -= ded
            deductions.append(f"-{ded} for {expired_docs} expired document(s)")
            
        # High mileage check
        if self.mileage_km > 150000:
            score -= 5
            deductions.append("-5 for high total mileage (>150k km)")

        # Failed inspections recently
        recent_fail = self.inspections.filter(overall_status='FAIL', inspect_date__gte=timezone.now().date() - timezone.timedelta(days=30)).count()
        if recent_fail > 0:
            ded = recent_fail * 12
            score -= ded
            deductions.append(f"-{ded} for recent failed digital inspection")

        final_score = max(20, min(100, score))
        return {
            'score': final_score,
            'deductions': deductions or ["No active risk factors. Vehicle in prime operating condition."]
        }


class Trip(models.Model):
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('ASSIGNED', 'Assigned'),
        ('STARTED', 'Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='trips')
    trip_id = models.CharField(max_length=50, unique=True)
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trips')
    
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    start_location = models.CharField(max_length=255, default="Origin Hub")
    destination = models.CharField(max_length=255, default="Destination Site")
    
    start_lat = models.FloatField(null=True, blank=True)
    start_lng = models.FloatField(null=True, blank=True)
    dest_lat = models.FloatField(null=True, blank=True)
    dest_lng = models.FloatField(null=True, blank=True)
    
    distance_km = models.FloatField(default=0.0)
    duration_minutes = models.IntegerField(default=0)
    idle_minutes = models.IntegerField(default=0)
    avg_speed_kmh = models.FloatField(default=0.0)
    max_speed_kmh = models.FloatField(default=0.0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip {self.trip_id} - {self.vehicle.vehicle_code} ({self.status})"


class GPSLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='gps_logs')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name='gps_logs')
    lat = models.FloatField()
    lng = models.FloatField()
    speed = models.FloatField(default=0.0)
    heading = models.FloatField(default=0.0)
    accuracy = models.FloatField(default=5.0) # meters
    battery_level = models.IntegerField(default=90)
    is_offline_synced = models.BooleanField(default=False)
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['recorded_at']

    def __str__(self):
        return f"GPS {self.vehicle.vehicle_code} @ {self.recorded_at.strftime('%H:%M:%S')} ({self.speed} km/h)"


class Geofence(models.Model):
    TYPE_CHOICES = (
        ('CIRCLE', 'Circular Zone'),
        ('POLYGON', 'Polygon Zone'),
    )
    CATEGORY_CHOICES = (
        ('WAREHOUSE', 'Warehouse / Depot'),
        ('OFFICE', 'Headquarters / Office'),
        ('SITE', 'Construction / Work Site'),
        ('RESTRICTED', 'Restricted Area'),
        ('PARKING', 'Parking Yard'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='geofences')
    name = models.CharField(max_length=150)
    geofence_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='CIRCLE')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='SITE')
    
    # Circle parameters
    center_lat = models.FloatField(null=True, blank=True)
    center_lng = models.FloatField(null=True, blank=True)
    radius_meters = models.FloatField(default=500.0)
    
    # Polygon parameters (JSON string of [{lat, lng}, ...])
    coordinates_json = models.TextField(blank=True, default='[]')
    
    entry_alert = models.BooleanField(default=True)
    exit_alert = models.BooleanField(default=True)
    dwell_alert = models.BooleanField(default=True)
    max_dwell_minutes = models.IntegerField(default=60)

    assigned_vehicles = models.ManyToManyField(Vehicle, blank=True, related_name='geofences')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class GeofenceLog(models.Model):
    EVENT_CHOICES = (
        ('ENTER', 'Geofence Entry'),
        ('EXIT', 'Geofence Exit'),
        ('DWELL', 'Excessive Dwell Time'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='geofence_logs')
    geofence = models.ForeignKey(Geofence, on_delete=models.CASCADE, related_name='logs')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='geofence_logs')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    dwell_duration_minutes = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.vehicle.vehicle_code} {self.event_type} {self.geofence.name} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class MaintenanceRecord(models.Model):
    TYPE_CHOICES = (
        ('ENGINE_SERVICE', 'Engine Service'),
        ('OIL_CHANGE', 'Oil & Filter Change'),
        ('BRAKE_SERVICE', 'Brake Service'),
        ('TYRE_REPLACEMENT', 'Tyre Replacement'),
        ('BATTERY', 'Battery Check/Replacement'),
        ('ENGINE_REPAIR', 'Engine Repair'),
        ('INSPECTION', 'General Inspection'),
        ('OTHER', 'Other Maintenance'),
    )
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='maintenance_records')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='ENGINE_SERVICE')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    
    odometer_at_service = models.FloatField(default=0.0)
    engine_hours_at_service = models.FloatField(default=0.0)
    
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    workshop_name = models.CharField(max_length=150, blank=True, default='In-House Garage')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    service_date = models.DateField(default=timezone.now)
    next_due_date = models.DateField(null=True, blank=True)
    next_due_km = models.FloatField(null=True, blank=True)
    next_due_engine_hours = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.total_cost = (self.parts_cost or 0) + (self.labor_cost or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle.vehicle_code} - {self.title} (${self.total_cost})"


class FuelLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='fuel_logs')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_logs')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='fuel_logs')
    
    date = models.DateField(default=timezone.now)
    fuel_quantity_liters = models.FloatField()
    price_per_liter = models.DecimalField(max_digits=8, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    odometer_km = models.FloatField(default=0.0)
    engine_hours = models.FloatField(default=0.0)
    fuel_station = models.CharField(max_length=150, blank=True, default='Shell Station')
    payment_method = models.CharField(max_length=50, default='Fuel Card')
    
    is_suspicious = models.BooleanField(default=False)
    suspicious_reason = models.CharField(max_length=255, blank=True, default='')

    def save(self, *args, **kwargs):
        if not self.total_cost and self.fuel_quantity_liters and self.price_per_liter:
            self.total_cost = self.fuel_quantity_liters * float(self.price_per_liter)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle.vehicle_code} - {self.fuel_quantity_liters}L (${self.total_cost}) on {self.date}"


class Expense(models.Model):
    CATEGORY_CHOICES = (
        ('FUEL', 'Fuel'),
        ('MAINTENANCE', 'Maintenance'),
        ('REPAIRS', 'Repairs'),
        ('TYRES', 'Tyres'),
        ('INSURANCE', 'Insurance'),
        ('TAX', 'Tax / License'),
        ('TOLL', 'Toll Fees'),
        ('PARKING', 'Parking'),
        ('DRIVER_EXPENSE', 'Driver Allowance'),
        ('PARTS', 'Parts & Supplies'),
        ('OTHER', 'Other'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='expenses')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='OTHER')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    notes = models.CharField(max_length=255, blank=True, default='')
    receipt_doc = models.FileField(upload_to='receipts/', null=True, blank=True)

    def __str__(self):
        return f"${self.amount} - {self.get_category_display()} ({self.date})"


class Document(models.Model):
    DOC_TYPES = (
        ('REGISTRATION', 'Vehicle Registration'),
        ('INSURANCE', 'Insurance Policy'),
        ('POLLUTION', 'Pollution Control (PUC)'),
        ('FITNESS', 'Fitness Certificate'),
        ('PERMIT', 'Route / Road Permit'),
        ('LICENSE', 'Driver License'),
        ('OTHER', 'Other Legal Document'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='documents')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    driver = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    
    title = models.CharField(max_length=150)
    doc_type = models.CharField(max_length=30, choices=DOC_TYPES, default='REGISTRATION')
    file = models.FileField(upload_to='documents/', null=True, blank=True)
    expiry_date = models.DateField()
    
    def status(self):
        today = timezone.now().date()
        if self.expiry_date < today:
            return 'EXPIRED'
        elif self.expiry_date <= today + timezone.timedelta(days=30):
            return 'EXPIRING_SOON'
        return 'VALID'

    def __str__(self):
        return f"{self.title} ({self.get_doc_type_display()}) - Exp: {self.expiry_date}"


class InspectionChecklist(models.Model):
    STATUS_CHOICES = (
        ('PASS', 'Passed Inspection'),
        ('FAIL', 'Failed - Maintenance Needed'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='inspections')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='inspections')
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inspections')
    inspect_date = models.DateTimeField(default=timezone.now)
    
    tyres_passed = models.BooleanField(default=True)
    brakes_passed = models.BooleanField(default=True)
    lights_passed = models.BooleanField(default=True)
    engine_passed = models.BooleanField(default=True)
    battery_passed = models.BooleanField(default=True)
    fuel_passed = models.BooleanField(default=True)
    mirrors_passed = models.BooleanField(default=True)
    body_passed = models.BooleanField(default=True)
    safety_passed = models.BooleanField(default=True)
    
    overall_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PASS')
    notes = models.TextField(blank=True, default='')
    photo = models.ImageField(upload_to='inspections/', null=True, blank=True)
    signature_data = models.TextField(blank=True, default='', help_text="Base64 Canvas signature")

    def __str__(self):
        return f"Inspection {self.vehicle.vehicle_code} by {self.driver.username} ({self.overall_status})"


class DispatchJob(models.Model):
    STATUS_CHOICES = (
        ('ASSIGNED', 'Assigned'),
        ('ACCEPTED', 'Accepted'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Completed / Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='dispatch_jobs')
    job_code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='jobs')
    
    destination_address = models.CharField(max_length=255)
    dest_lat = models.FloatField(null=True, blank=True)
    dest_lng = models.FloatField(null=True, blank=True)
    scheduled_time = models.DateTimeField()
    instructions = models.TextField(blank=True, default='')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')
    proof_photo = models.ImageField(upload_to='dispatch_proofs/', null=True, blank=True)
    customer_signature = models.TextField(blank=True, default='')
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Job {self.job_code}: {self.title} -> {self.driver.username}"


class Alert(models.Model):
    SEVERITY_CHOICES = (
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('DANGER', 'Critical Danger'),
    )
    ALERT_TYPES = (
        ('VEHICLE_OFFLINE', 'Vehicle Offline'),
        ('GEOFENCE_BREACH', 'Geofence Breach'),
        ('EXCESSIVE_IDLE', 'Excessive Idle Time'),
        ('MAINTENANCE_DUE', 'Maintenance Due'),
        ('DOCUMENT_EXPIRY', 'Document Expiry'),
        ('OVERSPEED', 'Overspeed Alert'),
        ('SUSPICIOUS_FUEL', 'Suspicious Fuel Entry'),
        ('INSPECTION_FAIL', 'Inspection Failure'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='alerts')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    driver = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=15, choices=SEVERITY_CHOICES, default='WARNING')
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity}] {self.title} - {self.created_at.strftime('%b %d, %H:%M')}"


class AuditLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=150)
    object_repr = models.CharField(max_length=200, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class Subscription(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('TRIAL', 'Trial'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    )
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='subscription')
    plan_name = models.CharField(max_length=50, default='Pro Fleet')
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2, default=99.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    current_period_end = models.DateField()

    def __str__(self):
        return f"{self.organization.name} - {self.plan_name} ({self.status})"
