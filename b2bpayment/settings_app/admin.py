from django.contrib import admin
from .models import BusinessSettings

@admin.register(BusinessSettings)
class BusinessSettingsAdmin(admin.ModelAdmin):
    list_display = ('business', 'upi_id', 'payee_name', 'reminder_before_due_days')
