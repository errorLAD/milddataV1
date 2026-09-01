from django.db import models
from core.models import TenantModel

class Tag(TenantModel):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, default='#4f46e5', verbose_name="Badge Color Hex")

    class Meta:
        ordering = ['name']
        unique_together = ['business', 'name']

    def __str__(self):
        return self.name

class WhatsAppMessageTemplate(TenantModel):
    TRIGGER_CHOICES = (
        ('Due Reminder', 'Due Reminder'),
        ('Overdue Reminder', 'Overdue Reminder'),
        ('Promise Confirmation', 'Promise Confirmation'),
        ('Payment Link', 'Payment Link'),
        ('Payment Received', 'Payment Received'),
        ('Sales Blast', 'Sales Blast'),
    )
    title = models.CharField(max_length=255)
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_CHOICES)
    content = models.TextField()

    def __str__(self):
        return f"{self.title} ({self.trigger_type})"

class WhatsAppConversation(TenantModel):
    CONVERSATION_TYPE_CHOICES = (
        ('recovery', 'Recovery/Udhaar'),
        ('sales', 'Sales/Product Inquiry'),
    )
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='whatsapp_conversations')
    conversation_type = models.CharField(max_length=20, choices=CONVERSATION_TYPE_CHOICES, default='recovery')
    is_human_takeover = models.BooleanField(default=False, verbose_name="Human Takeover (Pause AI Automation)")
    last_message_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message_at']
        unique_together = ['business', 'customer']

    def __str__(self):
        return f"Chat with {self.customer.name}"

class WhatsAppMessage(models.Model):
    SENDER_CHOICES = (
        ('business', 'Business'),
        ('customer', 'Customer'),
        ('system', 'System Automation'),
    )
    STATUS_CHOICES = (
        ('Sent', 'Sent'),
        ('Delivered', 'Delivered'),
        ('Read', 'Read'),
        ('Failed', 'Failed'),
    )
    conversation = models.ForeignKey(WhatsAppConversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES, default='business')
    message_text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Sent')
    
    # Voice Note handling
    is_voice_note = models.BooleanField(default=False)
    audio_file = models.FileField(upload_to='voice_notes/', null=True, blank=True)
    transcript = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.sender}] {self.message_text[:30]}"

class WhatsAppCampaign(TenantModel):
    TARGET_CHOICES = (
        ('all', 'All Marketing Opted-in Customers'),
        ('tag', 'Specific Customer Tag / Segment'),
        ('selected', 'Manually Selected Customers'),
    )
    title = models.CharField(max_length=255)
    message_text = models.TextField()
    image = models.ImageField(upload_to='campaigns/', blank=True, null=True)
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    target_tag = models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True, blank=True)
    sent_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Campaign: {self.title}"
