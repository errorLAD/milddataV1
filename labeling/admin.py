from django.contrib import admin

from .models import QuoteRequest


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "email",
        "data_type",
        "volume",
        "timeline",
        "created_at",
    )
    list_filter = ("data_type", "created_at")
    search_fields = ("company_name", "email", "message")
    readonly_fields = ("created_at",)
