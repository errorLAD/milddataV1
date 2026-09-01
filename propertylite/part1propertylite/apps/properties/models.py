from django.db import models
from apps.core.models import Organization, User
from builtins import property as py_property

class Property(models.Model):
    TYPE_APARTMENT = 'APARTMENT'
    TYPE_HOUSE = 'HOUSE'
    TYPE_VILLA = 'VILLA'
    TYPE_OFFICE = 'OFFICE'
    TYPE_SHOP = 'SHOP'
    TYPE_WAREHOUSE = 'WAREHOUSE'
    TYPE_COMMERCIAL = 'COMMERCIAL'
    TYPE_MIXED_USE = 'MIXED_USE'
    
    TYPE_CHOICES = [
        (TYPE_APARTMENT, 'Apartment Building'),
        (TYPE_HOUSE, 'Single Family House'),
        (TYPE_VILLA, 'Villa / Townhouse'),
        (TYPE_OFFICE, 'Office Complex'),
        (TYPE_SHOP, 'Retail Shop'),
        (TYPE_WAREHOUSE, 'Warehouse'),
        (TYPE_COMMERCIAL, 'Commercial Building'),
        (TYPE_MIXED_USE, 'Mixed-Use Property'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(max_length=255)
    property_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_APARTMENT)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='United States')
    
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='owned_properties',
        limit_choices_to={'role': User.ROLE_PROPERTY_OWNER}
    )
    manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='managed_properties',
        limit_choices_to={'role': User.ROLE_PROPERTY_MANAGER}
    )
    
    purchase_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    photo = models.ImageField(upload_to='property_photos/', null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Properties'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.city})"

    @py_property
    def total_units_count(self):
        return self.units.count()

    @py_property
    def occupied_units_count(self):
        return self.units.filter(status=Unit.STATUS_OCCUPIED).count()

    @py_property
    def vacant_units_count(self):
        return self.units.filter(status=Unit.STATUS_VACANT).count()

    @py_property
    def occupancy_rate(self):
        total = self.total_units_count
        if total == 0:
            return 0
        return round((self.occupied_units_count / total) * 100, 1)

class Building(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='buildings')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.property.name} - {self.name}"

class Unit(models.Model):
    STATUS_VACANT = 'VACANT'
    STATUS_OCCUPIED = 'OCCUPIED'
    STATUS_RESERVED = 'RESERVED'
    STATUS_MAINTENANCE = 'MAINTENANCE'
    STATUS_UNAVAILABLE = 'UNAVAILABLE'

    STATUS_CHOICES = [
        (STATUS_VACANT, 'Vacant'),
        (STATUS_OCCUPIED, 'Occupied'),
        (STATUS_RESERVED, 'Reserved'),
        (STATUS_MAINTENANCE, 'Under Maintenance'),
        (STATUS_UNAVAILABLE, 'Unavailable'),
    ]

    UNIT_TYPE_STUDIO = 'STUDIO'
    UNIT_TYPE_1BHK = '1BHK'
    UNIT_TYPE_2BHK = '2BHK'
    UNIT_TYPE_3BHK = '3BHK'
    UNIT_TYPE_COMMERCIAL = 'COMMERCIAL'

    UNIT_TYPE_CHOICES = [
        (UNIT_TYPE_STUDIO, 'Studio Apartment'),
        (UNIT_TYPE_1BHK, '1 Bedroom / 1 Bath'),
        (UNIT_TYPE_2BHK, '2 Bedroom / 2 Bath'),
        (UNIT_TYPE_3BHK, '3 Bedroom / 3 Bath'),
        (UNIT_TYPE_COMMERCIAL, 'Commercial Suite'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='units')
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True, related_name='units')
    unit_number = models.CharField(max_length=50)
    floor = models.IntegerField(default=1)
    type = models.CharField(max_length=30, choices=UNIT_TYPE_CHOICES, default=UNIT_TYPE_2BHK)
    area_sqft = models.IntegerField(default=850)
    bedrooms = models.IntegerField(default=2)
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1, default=2.0)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, default=1500.00)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=1500.00)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_VACANT)

    class Meta:
        ordering = ['unit_number']

    def __str__(self):
        return f"{self.property.name} - Unit {self.unit_number}"
