from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from apps.accounts.models import Organization
from apps.sales.models import Customer, Invoice
from apps.purchasing.models import Supplier, PurchaseBill

class Payment(models.Model):
    PAYMENT_TYPES = [
        ('RECEIVABLE', 'Customer Payment'),
        ('PAYABLE', 'Supplier Payment'),
    ]

    PAYMENT_METHODS = [
        ('Bank Transfer', 'Bank Transfer'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Cash', 'Cash'),
        ('Check', 'Check'),
        ('Wire Transfer', 'Wire Transfer'),
        ('Other', 'Other'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    bill = models.ForeignKey(PurchaseBill, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')

    payment_number = models.CharField(max_length=50)
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='Bank Transfer')
    reference = models.CharField(max_length=100, blank=True, default='')
    notes = models.TextField(blank=True, default='')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-id']

    def __str__(self):
        party = self.customer.company_name if self.customer else (self.supplier.company_name if self.supplier else 'N/A')
        return f"{self.payment_number} - {self.get_payment_type_display()} ({party}: {self.amount})"
