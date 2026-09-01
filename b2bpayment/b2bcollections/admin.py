from django.contrib import admin
from .models import ReminderRule, CollectionActivity


@admin.register(ReminderRule)
class ReminderRuleAdmin(admin.ModelAdmin):
    list_display = ['business', 'label', 'days_offset', 'is_enabled', 'order']
    list_filter = ['is_enabled', 'business']
    ordering = ['business', 'order']


@admin.register(CollectionActivity)
class CollectionActivityAdmin(admin.ModelAdmin):
    list_display = ['business', 'udhaar', 'activity_type', 'description', 'created_at']
    list_filter = ['activity_type', 'business']
    ordering = ['-created_at']
