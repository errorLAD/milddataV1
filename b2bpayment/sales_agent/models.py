from django.db import models
from core.models import TenantModel

class DraftOrder(TenantModel):
    STATUS_CHOICES = (
        ('Pending Owner Confirmation', 'Pending Owner Confirmation'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='draft_orders')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='draft_orders')
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending Owner Confirmation')
    notes = models.TextField(blank=True)
    converted_sale = models.ForeignKey('sales.Sale', on_delete=models.SET_NULL, null=True, blank=True, related_name='draft_orders')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        prod_name = self.product.name if self.product else "Item"
        return f"DraftOrder #{self.id} - {self.customer.name} ({self.quantity}x {prod_name}) [{self.status}]"

class SalesBlastHistory(TenantModel):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='blast_histories')
    template = models.ForeignKey('whatsapp.WhatsAppMessageTemplate', on_delete=models.SET_NULL, null=True, blank=True, related_name='blast_histories')
    recipient_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Blast #{self.id} - {self.product.name} ({self.recipient_count} sent)"

class CustomerProductBlastLog(TenantModel):
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='product_blast_logs')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='customer_blast_logs')
    last_blasted_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['business', 'customer', 'product']
        ordering = ['-last_blasted_at']

    def __str__(self):
        return f"BlastLog: {self.customer.name} - {self.product.name}"

class SalesAgentSettings(TenantModel):
    is_enabled = models.BooleanField(default=True, verbose_name="Enable AI Sales Agent")
    auto_draft_orders = models.BooleanField(default=True, verbose_name="Auto-Draft Orders for Owner Approval")
    greeting_message = models.TextField(
        default="Namaste! Main aapka AI Sales Assistant hu. Aap humare products ke baare me pooch sakte hain (Price, Stock, Order).",
        verbose_name="AI Greeting / Tone Message"
    )
    anti_spam_window_hours = models.IntegerField(default=24, verbose_name="Anti-Spam Window (Hours)")

    class Meta:
        verbose_name = "AI Sales Agent Settings"

    def __str__(self):
        return f"Sales Agent Settings ({self.business.name})"

class SalesAgentTemplate(TenantModel):
    MESSAGE_TYPE_CHOICES = (
        ('welcome', 'Welcome Message'),
        ('product_inquiry', 'Product Inquiry Response'),
        ('price_reply', 'Product Price Reply'),
        ('stock_reply', 'Stock Availability Reply'),
        ('recommendation', 'Product Recommendation'),
        ('customer_interested', 'Customer Interested / Quantity Prompt'),
        ('order_confirmation', 'Order Confirmation / Draft'),
        ('payment_message', 'Payment Message / Link'),
        ('order_status', 'Order Status Message'),
        ('followup', 'Follow-up Message'),
        ('out_of_stock', 'Out-of-Stock Message'),
        ('human_handoff', 'Human Handoff Message'),
        ('general', 'General AI Reply'),
    )

    name = models.CharField(max_length=255, verbose_name="Template Name")
    message_type = models.CharField(max_length=50, choices=MESSAGE_TYPE_CHOICES, verbose_name="Message Type")
    content = models.TextField(verbose_name="Message Template Content")
    is_active = models.BooleanField(default=True, verbose_name="Active Status")

    class Meta:
        ordering = ['message_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_message_type_display()})"
