from django.contrib import admin
from .models import WhatsAppMessageTemplate, WhatsAppConversation, WhatsAppMessage

@admin.register(WhatsAppMessageTemplate)
class WhatsAppMessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'trigger_type', 'business')
    list_filter = ('trigger_type', 'business')

@admin.register(WhatsAppConversation)
class WhatsAppConversationAdmin(admin.ModelAdmin):
    list_display = ('customer', 'is_human_takeover', 'last_message_at', 'business')
    list_filter = ('is_human_takeover', 'business')

@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'status', 'timestamp')
    list_filter = ('sender', 'status')
