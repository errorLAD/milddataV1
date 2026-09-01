from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'business', 'status', 'created_at')
    list_filter = ('business', 'status')
    search_fields = ('name', 'phone')
