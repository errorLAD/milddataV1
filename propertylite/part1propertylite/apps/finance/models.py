from django.db import models
from apps.core.models import Organization, User
from apps.properties.models import Property, Unit
from apps.leases.models import Lease
from builtins import property as py_property
from decimal import Decimal

class RentInvoice(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_PARTIALLY_PAID = 'PARTIALLY_PAID'
    STATUS_PAID = 'PAID'
    STATUS_OVERDUE = 'OVERDUE'
    STATUS_WAIVED = 'WAIVED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PARTIALLY_PAID, 'Partially Paid'),
        (STATUS_PAID, 'Paid'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_WAIVED, 'Waived'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invoices')
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='invoices')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='invoices')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    late_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    due_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.tenant.get_full_name()} (${self.amount})"

    @py_property
    def total_due(self):
        return Decimal(str(self.amount)) + Decimal(str(self.late_fee or 0))

    @py_property
    def total_paid(self):
        payments = self.payments.filter(status=Payment.STATUS_COMPLETED)
        return sum((p.amount for p in payments), Decimal('0.00'))

    @py_property
    def balance_due(self):
        return self.total_due - self.total_paid

class Payment(models.Model):
    METHOD_BANK_TRANSFER = 'BANK_TRANSFER'
    METHOD_CREDIT_CARD = 'CREDIT_CARD'
    METHOD_CASH = 'CASH'
    METHOD_UPI = 'UPI'
    METHOD_CHEQUE = 'CHEQUE'

    METHOD_CHOICES = [
        (METHOD_BANK_TRANSFER, 'Bank Transfer / ACH'),
        (METHOD_CREDIT_CARD, 'Credit Card'),
        (METHOD_CASH, 'Cash'),
        (METHOD_UPI, 'UPI / Instant Pay'),
        (METHOD_CHEQUE, 'Cheque'),
    ]

    STATUS_COMPLETED = 'COMPLETED'
    STATUS_PENDING = 'PENDING'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_FAILED, 'Failed'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(RentInvoice, on_delete=models.CASCADE, related_name='payments')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=30, choices=METHOD_CHOICES, default=METHOD_BANK_TRANSFER)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_COMPLETED)
    receipt_file = models.FileField(upload_to='receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment ${self.amount} for {self.invoice.invoice_number}"

class Expense(models.Model):
    CAT_MAINTENANCE = 'MAINTENANCE'
    CAT_UTILITIES = 'UTILITIES'
    CAT_PROPERTY_TAX = 'PROPERTY_TAX'
    CAT_INSURANCE = 'INSURANCE'
    CAT_CLEANING = 'CLEANING'
    CAT_SECURITY = 'SECURITY'
    CAT_STAFF = 'STAFF'
    CAT_VENDOR = 'VENDOR'
    CAT_REPAIRS = 'REPAIRS'
    CAT_OTHER = 'OTHER'

    CATEGORY_CHOICES = [
        (CAT_MAINTENANCE, 'Maintenance'),
        (CAT_UTILITIES, 'Utilities (Water/Electric/Gas)'),
        (CAT_PROPERTY_TAX, 'Property Tax'),
        (CAT_INSURANCE, 'Insurance'),
        (CAT_CLEANING, 'Cleaning & Janitorial'),
        (CAT_SECURITY, 'Security Services'),
        (CAT_STAFF, 'Staff Salaries'),
        (CAT_VENDOR, 'Vendor Contract'),
        (CAT_REPAIRS, 'Capital Repairs'),
        (CAT_OTHER, 'Other Expense'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='expenses')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CAT_MAINTENANCE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    vendor_name = models.CharField(max_length=150, blank=True, null=True)
    description = models.TextField()
    receipt = models.FileField(upload_to='expense_receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Expense ${self.amount} - {self.get_category_display()} ({self.property.name})"
