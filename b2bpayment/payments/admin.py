from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'amount', 'payment_method', 'status', 'verification_status', 'created_at')
    list_filter = ('payment_method', 'status', 'verification_status', 'business')
    search_fields = ('customer__name', 'reference_id')
