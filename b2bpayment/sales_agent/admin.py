from django.contrib import admin
from .models import DraftOrder, SalesBlastHistory, CustomerProductBlastLog, SalesAgentSettings, SalesAgentTemplate

@admin.register(DraftOrder)
class DraftOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'business', 'customer', 'product', 'quantity', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'business')
    search_fields = ('customer__name', 'product__name')

@admin.register(SalesBlastHistory)
class SalesBlastHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'business', 'product', 'recipient_count', 'reply_count', 'sent_at')

@admin.register(CustomerProductBlastLog)
class CustomerProductBlastLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'business', 'customer', 'product', 'last_blasted_at')

@admin.register(SalesAgentSettings)
class SalesAgentSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'business', 'is_enabled', 'auto_draft_orders', 'anti_spam_window_hours')

@admin.register(SalesAgentTemplate)
class SalesAgentTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'business', 'name', 'message_type', 'is_active')
    list_filter = ('message_type', 'is_active', 'business')
    search_fields = ('name', 'content')
