from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'selling_price', 'stock_quantity', 'business')
    list_filter = ('business', 'category')
    search_fields = ('name', 'sku')
