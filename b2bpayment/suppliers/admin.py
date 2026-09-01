from django.contrib import admin
from .models import Supplier, SupplierPurchase, SupplierPurchaseItem, SupplierPayment

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier_name', 'business', 'phone', 'business_name', 'total_purchases', 'total_paid', 'outstanding_payable', 'created_at')
    list_filter = ('business', 'created_at')
    search_fields = ('supplier_name', 'phone', 'business_name')

class SupplierPurchaseItemInline(admin.TabularInline):
    model = SupplierPurchaseItem
    extra = 1

@admin.register(SupplierPurchase)
class SupplierPurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'business', 'purchase_date', 'total_purchase', 'paid_amount', 'credit_amount', 'due_date', 'status')
    list_filter = ('business', 'status', 'due_date', 'purchase_date')
    search_fields = ('supplier__supplier_name', 'supplier__phone')
    inlines = [SupplierPurchaseItemInline]

@admin.register(SupplierPurchaseItem)
class SupplierPurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'purchase', 'business', 'product', 'quantity', 'cost_price', 'total')
    list_filter = ('business',)

@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'business', 'supplier_purchase', 'amount', 'date', 'payment_method', 'reference')
    list_filter = ('business', 'payment_method', 'date')
    search_fields = ('supplier__supplier_name', 'reference')
