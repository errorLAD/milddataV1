from django.contrib import admin

from .models import DemoLead, Order, Product


@admin.register(DemoLead)
class DemoLeadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "product_name",
        "email",
        "phone",
        "place",
        "created_at",
    )
    list_filter = ("product_name", "created_at")
    search_fields = ("full_name", "email", "phone", "place", "notes", "product_name")
    readonly_fields = ("created_at",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price_inr_monthly",
        "price_inr_yearly",
        "price_usd_monthly",
        "price_usd_yearly",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "billing_type", "is_active")
    search_fields = ("name", "description")
    list_editable = ("is_active",)

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "category", "description", "features", "access_info", "is_active"),
        }),
        ("India Regional Pricing (INR)", {
            "fields": ("price_inr_monthly", "price_inr_yearly", "gst_tax_rate"),
            "description": "Configure pricing for Indian customers. Default starting price is ₹199/month.",
        }),
        ("International Regional Pricing (USD)", {
            "fields": ("price_usd_monthly", "price_usd_yearly", "vat_tax_rate"),
            "description": "Configure pricing for international customers. Default starting price is $5/month.",
        }),
        ("Legacy / Base Fallback", {
            "classes": ("collapse",),
            "fields": ("price", "price_usd", "billing_type"),
        }),
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "customer_email",
        "currency",
        "total_amount",
        "payment_status",
        "created_at",
    )
    list_filter = ("payment_status", "currency", "billing_cycle", "created_at")
    search_fields = (
        "customer_email",
        "user__email",
        "razorpay_order_id",
        "razorpay_payment_id",
    )
    readonly_fields = (
        "product",
        "user",
        "customer_email",
        "region",
        "currency",
        "billing_cycle",
        "subtotal_amount",
        "tax_amount",
        "total_amount",
        "amount_paid",
        "razorpay_order_id",
        "razorpay_payment_id",
        "created_at",
    )
