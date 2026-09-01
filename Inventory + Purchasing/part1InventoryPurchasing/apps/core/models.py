from django.db import models
from django.contrib.auth.models import User
from apps.accounts.models import Organization

class TaxRule(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='tax_rules')
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    is_compound = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

class Notification(models.Model):
    TYPES = [
        ('LOW_STOCK', 'Low Stock Alert'),
        ('OUT_OF_STOCK', 'Out of Stock Alert'),
        ('INVOICE_DUE', 'Invoice Due'),
        ('INVOICE_OVERDUE', 'Invoice Overdue'),
        ('PO_RECEIVED', 'Purchase Order Received'),
        ('PAYMENT_RECEIVED', 'Payment Received'),
        ('SUPPLIER_PAYMENT_DUE', 'Supplier Payment Due'),
        ('STOCK_TRANSFER', 'Stock Transfer Completed'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.title}"

class AuditLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_actions')
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=255)
    details = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M')} - {self.action} by {self.user}"

class OrganizationAISetting(models.Model):
    PROVIDERS = [
        ('GEMINI', 'Google Gemini AI'),
        ('OPENAI', 'OpenAI (GPT-4o / GPT-3.5)'),
        ('ANTHROPIC', 'Anthropic Claude'),
        ('OLLAMA', 'Local Ollama / Custom API'),
        ('BUILTIN', 'StockFlow Built-in Intelligent Copilot'),
    ]

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='ai_setting')
    provider = models.CharField(max_length=20, choices=PROVIDERS, default='BUILTIN')
    api_key = models.CharField(max_length=255, blank=True, default='')
    model_name = models.CharField(max_length=100, default='gemini-1.5-flash')
    is_enabled = models.BooleanField(default=True)
    max_daily_queries = models.IntegerField(default=100)
    custom_system_prompt = models.TextField(blank=True, default='You are StockFlow AI, an executive inventory and financial copilot for growing SMBs.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.organization.name} - AI Settings ({self.get_provider_display()})"

class AIUsageLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='ai_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    prompt = models.TextField()
    response = models.TextField()
    has_action_proposal = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
