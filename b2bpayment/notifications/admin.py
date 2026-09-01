from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_read', 'business', 'created_at')
    list_filter = ('category', 'is_read', 'business')
