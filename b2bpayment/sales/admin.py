from django.contrib import admin
from .models import Sale, SaleItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'total_amount', 'paid_amount', 'udhaar_amount', 'payment_method', 'sale_date')
    list_filter = ('payment_method', 'business')
    search_fields = ('invoice_number', 'customer__name')
    inlines = [SaleItemInline]
