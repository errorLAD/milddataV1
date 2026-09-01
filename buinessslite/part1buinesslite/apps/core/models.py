from django.db import models
from django.contrib.auth.models import User

class Organization(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, default="United States")
    currency_code = models.CharField(max_length=10, default="USD")
    currency_symbol = models.CharField(max_length=10, default="$")
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(max_length=10, default="en")
    date_format = models.CharField(max_length=20, default="YYYY-MM-DD")
    number_format = models.CharField(max_length=20, default="1,000.00")
    tax_name = models.CharField(max_length=50, default="Sales Tax")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    tax_inclusive = models.BooleanField(default=False)
    invoice_prefix = models.CharField(max_length=20, default="INV-")
    quote_prefix = models.CharField(max_length=20, default="QT-")
    order_prefix = models.CharField(max_length=20, default="SO-")
    po_prefix = models.CharField(max_length=20, default="PO-")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserRole(models.TextChoices):
    OWNER = 'OWNER', 'Owner'
    ADMIN = 'ADMIN', 'Admin'
    MANAGER = 'MANAGER', 'Manager'
    EMPLOYEE = 'EMPLOYEE', 'Employee'
    ACCOUNTANT = 'ACCOUNTANT', 'Accountant'
    SALES = 'SALES', 'Sales User'
    WAREHOUSE = 'WAREHOUSE', 'Warehouse User'
    VIEWER = 'VIEWER', 'Viewer'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.OWNER)
    phone = models.CharField(max_length=50, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.role}) - {self.organization.name if self.organization else 'No Org'}"

class AuditLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"

class NotificationType(models.TextChoices):
    OVERDUE_INVOICE = 'OVERDUE_INVOICE', 'Invoice Overdue'
    LOW_STOCK = 'LOW_STOCK', 'Product Low Stock'
    EMPLOYEE_ABSENT = 'EMPLOYEE_ABSENT', 'Employee Absent'
    EXPIRING_DOC = 'EXPIRING_DOC', 'Document Expiring'
    PO_RECEIVED = 'PO_RECEIVED', 'Purchase Received'
    PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Payment Received'
    SYSTEM = 'SYSTEM', 'System Alert'

class Notification(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.organization.name}"
