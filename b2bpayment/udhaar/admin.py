from django.contrib import admin
from .models import Udhaar

@admin.register(Udhaar)
class UdhaarAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'total_amount', 'paid_amount', 'remaining_amount', 'due_date', 'status', 'business')
    list_filter = ('status', 'verification_status', 'business')
    search_fields = ('customer__name', 'customer__phone')
