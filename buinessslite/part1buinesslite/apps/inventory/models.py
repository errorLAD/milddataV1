from django.db import models
from django.contrib.auth.models import User
from apps.core.models import Organization

class ProductCategory(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='product_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Warehouse(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=150)
    location_code = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class ProductType(models.TextChoices):
    PHYSICAL = 'PHYSICAL', 'Physical Stock'
    SERVICE = 'SERVICE', 'Service'
    NON_STOCK = 'NON_STOCK', 'Non-Stock Item'

class Product(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=20, default='pcs')
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reorder_level = models.IntegerField(default=5)
    stock_quantity = models.IntegerField(default=0)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    product_type = models.CharField(max_length=20, choices=ProductType.choices, default=ProductType.PHYSICAL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_low_stock(self):
        if self.product_type != ProductType.PHYSICAL:
            return False
        return self.stock_quantity <= self.reorder_level

class MovementType(models.TextChoices):
    STOCK_IN = 'STOCK_IN', 'Stock In'
    STOCK_OUT = 'STOCK_OUT', 'Stock Out'
    ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
    TRANSFER = 'TRANSFER', 'Transfer'
    RETURN = 'RETURN', 'Return'
    DAMAGE = 'DAMAGE', 'Damage / Waste'

class StockMovement(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='stock_movements')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    quantity_change = models.IntegerField()
    movement_type = models.CharField(max_length=20, choices=MovementType.choices, default=MovementType.ADJUSTMENT)
    reference = models.CharField(max_length=150, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name}: {self.quantity_change:+d} ({self.movement_type})"
