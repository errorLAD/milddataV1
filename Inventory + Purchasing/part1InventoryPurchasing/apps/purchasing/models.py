from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from apps.accounts.models import Organization
from apps.inventory.models import Product, Warehouse

class Supplier(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='suppliers')
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=150, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    website = models.URLField(blank=True, default='')
    country = models.CharField(max_length=100, default='United States')
    address = models.TextField(blank=True, default='')
    payment_terms = models.CharField(max_length=50, default='Net 30')
    currency = models.CharField(max_length=10, default='USD')
    tax_id = models.CharField(max_length=100, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name

    @property
    def total_purchases(self):
        return sum(po.total_amount for po in self.purchase_orders.filter(status__in=['APPROVED', 'PARTIALLY_RECEIVED', 'COMPLETED']))

    @property
    def outstanding_payables(self):
        return sum(b.remaining_balance for b in self.bills.filter(status__in=['OPEN', 'PARTIALLY_PAID', 'OVERDUE']))

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent to Supplier'),
        ('APPROVED', 'Approved'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    po_number = models.CharField(max_length=50, db_index=True)
    order_date = models.DateField()
    expected_delivery = models.DateField(null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='purchase_orders')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    payment_terms = models.CharField(max_length=50, default='Net 30')
    notes = models.TextField(blank=True, default='')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date', '-id']
        unique_together = ('organization', 'po_number')

    def __str__(self):
        return f"{self.po_number} - {self.supplier.company_name}"

    def recalculate_totals(self):
        sub = Decimal('0.00')
        tax = Decimal('0.00')
        for item in self.items.all():
            sub += Decimal(str(item.quantity)) * Decimal(str(item.unit_cost)) - Decimal(str(item.discount))
            tax += (Decimal(str(item.quantity)) * Decimal(str(item.unit_cost)) - Decimal(str(item.discount))) * (Decimal(str(item.tax_rate)) / Decimal('100.0'))
        self.subtotal = sub
        self.tax_amount = tax
        self.total_amount = sub + tax + Decimal(str(self.shipping_amount)) - Decimal(str(self.discount_amount))
        self.save()

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    received_quantity = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    @property
    def remaining_quantity(self):
        return max(0, self.quantity - self.received_quantity)

    def save(self, *args, **kwargs):
        line_sub = (Decimal(str(self.quantity)) * Decimal(str(self.unit_cost))) - Decimal(str(self.discount))
        line_tax = line_sub * (Decimal(str(self.tax_rate)) / Decimal('100.0'))
        self.total = line_sub + line_tax
        super().save(*args, **kwargs)

class GoodsReceipt(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='goods_receipts')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='goods_receipts')
    receipt_number = models.CharField(max_length=50)
    receipt_date = models.DateField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.receipt_number} (PO: {self.purchase_order.po_number})"

class GoodsReceiptItem(models.Model):
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='items')
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_received = models.IntegerField()

class PurchaseBill(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('OPEN', 'Open'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='bills')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='bills')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='bills')
    bill_number = models.CharField(max_length=50)
    bill_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='OPEN')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-bill_date', '-id']

    def __str__(self):
        return f"{self.bill_number} - {self.supplier.company_name}"

    @property
    def remaining_balance(self):
        return max(Decimal('0.00'), Decimal(str(self.total_amount)) - Decimal(str(self.paid_amount)))
