from django.db import models
from apps.core.models import Organization, User
from apps.properties.models import Property, Unit
from builtins import property as py_property

class Vendor(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='vendors')
    name = models.CharField(max_length=150)
    company = models.CharField(max_length=150)
    category = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    address = models.CharField(max_length=255, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company} ({self.name})"

class MaintenanceTicket(models.Model):
    CAT_PLUMBING = 'PLUMBING'
    CAT_ELECTRICAL = 'ELECTRICAL'
    CAT_HVAC = 'HVAC'
    CAT_CLEANING = 'CLEANING'
    CAT_APPLIANCE = 'APPLIANCE'
    CAT_STRUCTURAL = 'STRUCTURAL'
    CAT_SECURITY = 'SECURITY'
    CAT_OTHER = 'OTHER'

    CATEGORY_CHOICES = [
        (CAT_PLUMBING, 'Plumbing'),
        (CAT_ELECTRICAL, 'Electrical'),
        (CAT_HVAC, 'Heating & Air Conditioning (HVAC)'),
        (CAT_CLEANING, 'Cleaning'),
        (CAT_APPLIANCE, 'Appliance Repair'),
        (CAT_STRUCTURAL, 'Structural / Carpentry'),
        (CAT_SECURITY, 'Security & Locks'),
        (CAT_OTHER, 'General Maintenance'),
    ]

    PRIORITY_LOW = 'LOW'
    PRIORITY_MEDIUM = 'MEDIUM'
    PRIORITY_HIGH = 'HIGH'
    PRIORITY_EMERGENCY = 'EMERGENCY'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_EMERGENCY, 'Emergency'),
    ]

    STATUS_NEW = 'NEW'
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_WAITING = 'WAITING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_WAITING, 'Waiting on Parts'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='tickets')
    title = models.CharField(max_length=255)
    description = models.TextField()
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='tickets')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='tickets')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_tickets')
    
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CAT_PLUMBING)
    priority = models.CharField(max_length=30, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_NEW)
    
    assigned_staff = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tickets',
        limit_choices_to={'role': User.ROLE_MAINTENANCE_STAFF}
    )
    assigned_vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    photo = models.ImageField(upload_to='maintenance_photos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.id}: {self.title} ({self.get_status_display()})"

    @py_property
    def materials_cost(self):
        return sum(m.total_cost for m in self.materials.all())

    @py_property
    def labour_cost(self):
        return sum(l.total_cost for l in self.labour_items.all())

    @py_property
    def actual_total_cost(self):
        return self.materials_cost + self.labour_cost

class TicketMaterial(models.Model):
    ticket = models.ForeignKey(MaintenanceTicket, on_delete=models.CASCADE, related_name='materials')
    material_name = models.CharField(max_length=150)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1.0)
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    @py_property
    def total_cost(self):
        return self.quantity * self.unit_cost

    def __str__(self):
        return f"{self.material_name} x {self.quantity}"

class TicketLabour(models.Model):
    ticket = models.ForeignKey(MaintenanceTicket, on_delete=models.CASCADE, related_name='labour_items')
    worker_name = models.CharField(max_length=150)
    hours = models.DecimalField(max_digits=6, decimal_places=2, default=1.0)
    rate = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    @py_property
    def total_cost(self):
        return self.hours * self.rate

    def __str__(self):
        return f"{self.worker_name} ({self.hours} hrs)"
