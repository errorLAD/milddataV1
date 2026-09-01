from django.db import models
from apps.tenants.models import Organization
from apps.machines.models import Machine

class SparePart(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='spare_parts')
    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=50)
    category = models.CharField(max_length=50, default='Filters & Fluids')
    stock_quantity = models.IntegerField(default=10)
    min_stock_threshold = models.IntegerField(default=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=1500.00)
    supplier_name = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (SKU: {self.sku}) - Qty: {self.stock_quantity}"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_threshold

class PartTransaction(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='part_transactions')
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='transactions')
    machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=(('stock_in', 'Stock IN'), ('stock_out', 'Stock OUT')))
    quantity = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-date']
