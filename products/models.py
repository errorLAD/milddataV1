from decimal import Decimal
from django.conf import settings
from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("ai_agent", "AI Agent"),
        ("saas_tool", "SaaS Tool"),
    ]
    BILLING_TYPE_CHOICES = [
        ("one_time", "One-time"),
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    features = models.TextField(
        blank=True,
        help_text="One feature per line",
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Base fallback prices
    price = models.DecimalField(max_digits=10, decimal_places=2, default=199.00, help_text="Base Price (INR)")
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, help_text="Base Price (USD)")
    
    # Regional Admin-Configurable Monthly & Yearly Prices
    price_inr_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=199.00, help_text="India Monthly Price (₹)")
    price_inr_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=1982.00, help_text="India Yearly Price (₹199*12 with 17% discount)")
    price_usd_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, help_text="International Monthly Price ($)")
    price_usd_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=49.80, help_text="International Yearly Price ($5*12 with 17% discount)")

    # Regional Admin-Configurable Tax Rates (%)
    gst_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00, help_text="India GST Tax Rate (%)")
    vat_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="International Tax/VAT Rate (%)")

    billing_type = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES, default="monthly")
    access_info = models.TextField(
        blank=True,
        help_text="Shown to customer after successful payment",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_features_list(self):
        if not self.features:
            return []
        return [f.strip() for f in self.features.splitlines() if f.strip()]

    def get_price_amount(self, currency="INR", billing_cycle="monthly"):
        """Get exact numeric price based on currency (INR/USD) and billing cycle (monthly/yearly)."""
        cycle = billing_cycle.lower() if billing_cycle in ("monthly", "yearly") else "monthly"
        curr = currency.upper() if currency in ("INR", "USD") else "INR"

        if curr == "USD":
            return self.price_usd_yearly if cycle == "yearly" else self.price_usd_monthly
        return self.price_inr_yearly if cycle == "yearly" else self.price_inr_monthly

    def get_display_price(self, currency="INR", billing_cycle="monthly"):
        """Format display price string with discounts."""
        cycle = billing_cycle.lower() if billing_cycle in ("monthly", "yearly") else "monthly"
        curr = currency.upper() if currency in ("INR", "USD") else "INR"

        if curr == "USD":
            if cycle == "yearly":
                return f"${self.price_usd_yearly:,.2f}/yr (Save 17%)"
            return f"${self.price_usd_monthly:,.0f}/mo"
        else:
            if cycle == "yearly":
                return f"₹{self.price_inr_yearly:,.0f}/yr (Save 17%)"
            return f"₹{self.price_inr_monthly:,.0f}/mo"

    def get_tax_breakdown(self, currency="INR", billing_cycle="monthly"):
        """
        Calculate authoritative server-side price, tax, and total.
        Returns tuple: (subtotal, tax_amount, total_amount, tax_rate_percent)
        """
        subtotal = self.get_price_amount(currency, billing_cycle)
        tax_rate = self.gst_tax_rate if currency == "INR" else self.vat_tax_rate
        tax_amount = (subtotal * tax_rate) / Decimal("100.00")
        total = subtotal + tax_amount
        return subtotal, tax_amount.quantize(Decimal("0.01")), total.quantize(Decimal("0.01")), tax_rate

    @property
    def price_display(self):
        return self.get_display_price(currency="INR", billing_cycle="monthly")

    @property
    def price_in_paise(self):
        return int(self.price_inr_monthly * 100)


class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]
    BILLING_CYCLE_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="orders")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True,
    )
    customer_email = models.EmailField()
    region = models.CharField(max_length=10, default="IN")
    currency = models.CharField(max_length=10, default="INR")
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLE_CHOICES, default="monthly")
    
    # Financial line items
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} — {self.product.name} ({self.currency} {self.total_amount} {self.payment_status})"


class DemoLead(models.Model):
    product_name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    place = models.CharField(max_length=200, help_text="Location / City / Country")
    notes = models.TextField(blank=True, help_text="Specific requirements / business notes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Demo Lead: {self.full_name} ({self.product_name}) - {self.place}"
