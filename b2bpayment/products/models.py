from django.db import models
from core.models import TenantModel

class Product(TenantModel):
    name = models.CharField(max_length=255, verbose_name="Product Name")
    sku = models.CharField(max_length=100, blank=True, verbose_name="SKU Code")
    barcode = models.CharField(max_length=100, blank=True, verbose_name="Barcode / EAN Number")
    category = models.CharField(max_length=100, blank=True, verbose_name="Category")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Selling Price (₹)")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Cost Price (₹)")
    stock_quantity = models.IntegerField(default=0, verbose_name="Stock Quantity")
    low_stock_threshold = models.IntegerField(default=5, verbose_name="Low Stock Threshold")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (Stock: {self.stock_quantity})"

    @property
    def is_out_of_stock(self):
        return self.stock_quantity <= 0

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def stock_status(self):
        if self.stock_quantity <= 0:
            return 'Out of Stock'
        elif self.stock_quantity <= self.low_stock_threshold:
            return 'Low Stock'
        return 'In Stock'
