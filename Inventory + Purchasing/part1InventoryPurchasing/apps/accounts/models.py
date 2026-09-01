from django.db import models
from django.contrib.auth.models import User

class Organization(models.Model):
    CURRENCY_POSITIONS = [
        ('prefix', 'Prefix ($100)'),
        ('suffix', 'Suffix (100€)'),
    ]

    DATE_FORMATS = [
        ('MM/DD/YYYY', 'MM/DD/YYYY (US, CA)'),
        ('DD/MM/YYYY', 'DD/MM/YYYY (UK, AU, NZ)'),
        ('DD.MM.YYYY', 'DD.MM.YYYY (DE, EU)'),
        ('YYYY-MM-DD', 'YYYY-MM-DD (ISO standard)'),
    ]

    NUMBER_FORMATS = [
        ('1,234.56', '1,234.56 (Standard)'),
        ('1.234,56', '1.234,56 (European)'),
        ('1 234,56', '1 234,56 (Space separator)'),
    ]

    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, default='United States')
    currency_code = models.CharField(max_length=10, default='USD')
    currency_symbol = models.CharField(max_length=10, default='$')
    currency_position = models.CharField(max_length=10, choices=CURRENCY_POSITIONS, default='prefix')
    decimal_places = models.IntegerField(default=2)

    date_format = models.CharField(max_length=20, choices=DATE_FORMATS, default='MM/DD/YYYY')
    number_format = models.CharField(max_length=20, choices=NUMBER_FORMATS, default='1,234.56')
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=20, default='en')

    # Configurable Tax System
    tax_name = models.CharField(max_length=50, default='Sales Tax')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=8.50)
    tax_id_label = models.CharField(max_length=50, default='Tax ID')
    tax_id_value = models.CharField(max_length=100, blank=True, default='')
    tax_inclusive = models.BooleanField(default=False)

    # Document Prefix Settings
    invoice_prefix = models.CharField(max_length=20, default='INV-')
    po_prefix = models.CharField(max_length=20, default='PO-')
    quote_prefix = models.CharField(max_length=20, default='QT-')
    order_prefix = models.CharField(max_length=20, default='SO-')
    bill_prefix = models.CharField(max_length=20, default='BILL-')

    # Contact & Address
    address = models.TextField(blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    website = models.URLField(blank=True, default='')
    logo = models.ImageField(upload_to='org_logos/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    ROLES = [
        ('OWNER', 'Owner'),
        ('ADMIN', 'Administrator'),
        ('SALES_MANAGER', 'Sales Manager'),
        ('PURCHASING_MANAGER', 'Purchasing Manager'),
        ('WAREHOUSE_MANAGER', 'Warehouse Manager'),
        ('SALES_USER', 'Sales User'),
        ('WAREHOUSE_USER', 'Warehouse User'),
        ('ACCOUNTANT', 'Accountant'),
        ('VIEWER', 'Viewer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=30, choices=ROLES, default='OWNER')
    phone = models.CharField(max_length=50, blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"
