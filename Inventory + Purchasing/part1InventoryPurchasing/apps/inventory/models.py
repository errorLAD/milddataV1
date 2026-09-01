from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from apps.accounts.models import Organization

class ProductCategory(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = 'Product Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class ProductUnit(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=50) # e.g. Piece, Box, Kilogram, Hour
    abbreviation = models.CharField(max_length=15) # e.g. pcs, box, kg, hr

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class Product(models.Model):
    PRODUCT_TYPES = [
        ('PHYSICAL', 'Physical Product'),
        ('SERVICE', 'Service'),
        ('NON_STOCK', 'Non-Stock Item'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, default='', db_index=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='PHYSICAL')

    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    unit = models.ForeignKey(ProductUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    brand = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField(blank=True, default='')

    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    tax_category = models.CharField(max_length=50, default='Standard Rate')
    reorder_level = models.IntegerField(default=10)
    opening_stock = models.IntegerField(default=0)
    is_archived = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ('organization', 'sku')

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def total_stock(self):
        if self.product_type != 'PHYSICAL':
            return 99999
        return sum(item.quantity for item in self.inventory_levels.all())

    @property
    def reserved_stock(self):
        if self.product_type != 'PHYSICAL':
            return 0
        return sum(item.reserved_quantity for item in self.inventory_levels.all())

    @property
    def available_stock(self):
        return max(0, self.total_stock - self.reserved_stock)

    @property
    def inventory_value(self):
        if self.product_type != 'PHYSICAL':
            return Decimal('0.00')
        return Decimal(self.total_stock) * self.purchase_price

    @property
    def status(self):
        if self.product_type != 'PHYSICAL':
            return 'In Stock'
        total = self.total_stock
        if total <= 0:
            return 'Out of Stock'
        elif total <= self.reorder_level:
            return 'Low Stock'
        return 'In Stock'

class Warehouse(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    address = models.TextField(blank=True, default='')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'name']
        unique_together = ('organization', 'code')

    def __str__(self):
        return f"{self.name} ({self.code})"

class Inventory(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='inventories')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_levels')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory_levels')
    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ('product', 'warehouse')
        verbose_name_plural = 'Inventories'

    @property
    def available_quantity(self):
        return max(0, self.quantity - self.reserved_quantity)

    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name}: {self.quantity}"

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('PURCHASE', 'Purchase Receipt'),
        ('SALE', 'Sales Invoice'),
        ('RETURN', 'Sales Return'),
        ('ADJUSTMENT', 'Stock Adjustment'),
        ('TRANSFER', 'Warehouse Transfer'),
        ('DAMAGE', 'Damage / Expiry'),
        ('CORRECTION', 'Inventory Correction'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='stock_movements')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField() # Positive for add, negative for deduct
    quantity_before = models.IntegerField()
    quantity_after = models.IntegerField()
    reference = models.CharField(max_length=100, blank=True, default='') # PO number, Invoice number, etc.
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d')} | {self.product.sku} | {self.get_movement_type_display()} ({self.quantity:+d})"
