import datetime
from django.db import models
from django.utils import timezone
from django.db.models import Sum
from core.models import TenantModel

class Supplier(TenantModel):
    supplier_name = models.CharField(max_length=255, verbose_name="Supplier Name")
    phone = models.CharField(max_length=20, verbose_name="Phone Number")
    business_name = models.CharField(max_length=255, blank=True, verbose_name="Company / Firm Name")
    address = models.TextField(blank=True, verbose_name="Address")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.business_name:
            return f"{self.supplier_name} ({self.business_name})"
        return self.supplier_name

    @property
    def total_purchases(self):
        val = sum([p.effective_total_purchase for p in self.purchases.all()])
        return float(val)

    @property
    def total_paid(self):
        initial_paid = self.purchases.aggregate(s=Sum('paid_amount'))['s'] or 0
        payments_sum = self.payments.aggregate(s=Sum('amount'))['s'] or 0
        return float(initial_paid + payments_sum)

    @property
    def outstanding_payable(self):
        val = sum([p.remaining_payable for p in self.purchases.exclude(status='Paid')])
        return round(val, 2)

    @property
    def overdue_payable(self):
        val = sum([p.remaining_payable for p in self.purchases.filter(status='Overdue')])
        return round(val, 2)

class SupplierPurchase(TenantModel):
    STATUS_CHOICES = (
        ('Due', 'Due'),
        ('Overdue', 'Overdue'),
        ('Partially Paid', 'Partially Paid'),
        ('Payment Promised', 'Payment Promised'),
        ('Paid', 'Paid'),
        ('Disputed', 'Disputed'),
    )

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchases')
    purchase_date = models.DateTimeField(default=timezone.now)
    total_purchase = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Due')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return f"Purchase #{self.pk} - {self.supplier.supplier_name} (₹{self.total_purchase})"

    @property
    def effective_total_purchase(self):
        eff = max(float(self.total_purchase), float(self.paid_amount) + float(self.credit_amount))
        return round(eff, 2)

    @property
    def remaining_payable(self):
        payments_sum = self.payments.aggregate(s=Sum('amount'))['s'] or 0
        eff_total = self.effective_total_purchase
        tot_paid = float(self.paid_amount) + float(payments_sum)
        rem = eff_total - tot_paid
        return max(0.0, round(rem, 2))

    @property
    def days_overdue(self):
        if self.due_date and self.remaining_payable > 0:
            today = timezone.now().date()
            d_date = self.due_date
            if isinstance(d_date, str):
                try:
                    d_date = datetime.datetime.strptime(d_date, '%Y-%m-%d').date()
                except ValueError:
                    return 0
            if today > d_date:
                return (today - d_date).days
        return 0

    def update_status(self):
        eff_total = self.effective_total_purchase
        if float(self.total_purchase) < eff_total:
            self.total_purchase = eff_total

        today = timezone.now().date()
        rem = self.remaining_payable
        d_date = self.due_date
        if isinstance(d_date, str):
            try:
                d_date = datetime.datetime.strptime(d_date, '%Y-%m-%d').date()
            except ValueError:
                d_date = None

        if rem <= 0:
            self.status = 'Paid'
        elif d_date and today > d_date:
            self.status = 'Overdue'
        elif float(self.paid_amount) > 0 or self.payments.exists():
            self.status = 'Partially Paid'
        else:
            self.status = 'Due'
        self.save(update_fields=['total_purchase', 'status'])

class SupplierPurchaseItem(TenantModel):
    purchase = models.ForeignKey(SupplierPurchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, related_name='supplier_purchase_items')
    quantity = models.IntegerField(default=1)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.cost_price
        super().save(*args, **kwargs)

    def __str__(self):
        p_name = self.product.name if self.product else "Item"
        return f"{self.quantity}x {p_name} @ ₹{self.cost_price}"

class SupplierPayment(TenantModel):
    PAYMENT_METHOD_CHOICES = (
        ('UPI', 'UPI'),
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Online Payment', 'Online Payment'),
        ('Other', 'Other'),
    )

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='payments')
    supplier_purchase = models.ForeignKey(SupplierPurchase, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='UPI')
    reference = models.CharField(max_length=100, blank=True, verbose_name="Transaction Reference / UTR")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Supplier Payment ₹{self.amount} to {self.supplier.supplier_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.supplier_purchase:
            self.supplier_purchase.update_status()
