from django.db import models
from core.models import TenantModel


class ReminderRule(TenantModel):
    """
    Configurable reminder schedule for automatic WhatsApp reminders.
    days_offset: negative = before due date, positive = after due date
    Example: -3 = "3 days before due", +7 = "7 days overdue"
    """
    days_offset = models.IntegerField(
        verbose_name="Days Offset",
        help_text="Negative = before due date, Positive = days overdue"
    )
    label = models.CharField(
        max_length=100,
        verbose_name="Rule Label",
        help_text="e.g. '3 days before due', '7 days overdue'"
    )
    template = models.ForeignKey(
        'whatsapp.WhatsAppMessageTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reminder_rules',
        verbose_name="Message Template"
    )
    is_enabled = models.BooleanField(default=True, verbose_name="Enabled")
    order = models.IntegerField(default=0, verbose_name="Display Order")

    class Meta:
        ordering = ['order', 'days_offset']
        verbose_name = "Reminder Rule"
        verbose_name_plural = "Reminder Rules"

    def __str__(self):
        status = "✅" if self.is_enabled else "⏸"
        prefix = "Before" if self.days_offset < 0 else "After"
        return f"{status} {abs(self.days_offset)} days {prefix} due — {self.label}"

    @property
    def description(self):
        if self.days_offset == 0:
            return "On the due date"
        elif self.days_offset < 0:
            return f"{abs(self.days_offset)} days before due date"
        else:
            return f"{self.days_offset} days after due date (overdue)"


class CollectionActivity(TenantModel):
    """
    Audit log / timeline for each collection (Udhaar).
    Records every action: reminder sent, promise made, payment received, etc.
    """
    ACTIVITY_TYPES = (
        ('invoice_created', '📄 Invoice Created'),
        ('collection_created', '📋 Collection Added'),
        ('reminder_sent', '📲 Reminder Sent'),
        ('promise_made', '🤝 Payment Promised'),
        ('promise_missed', '⚠️ Promise Missed'),
        ('partial_payment', '💰 Partial Payment Received'),
        ('full_payment', '✅ Payment Received (Full)'),
        ('due_date_changed', '📅 Due Date Changed'),
        ('status_changed', '🔄 Status Updated'),
        ('note_added', '📝 Note Added'),
        ('escalated', '🚨 Escalated'),
        ('disputed', '❌ Disputed'),
    )

    udhaar = models.ForeignKey(
        'udhaar.Udhaar',
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name="Collection (Udhaar)"
    )
    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPES,
        default='note_added',
        verbose_name="Activity Type"
    )
    description = models.TextField(verbose_name="Description")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Amount (if applicable)"
    )
    performed_by = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Performed By",
        help_text="Username or 'System Auto'"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Collection Activity"
        verbose_name_plural = "Collection Activities"

    def __str__(self):
        return f"[{self.activity_type}] {self.udhaar.customer.name} — {self.description[:40]}"

    @property
    def icon(self):
        icons = {
            'invoice_created': 'bi-file-earmark-text',
            'collection_created': 'bi-plus-circle',
            'reminder_sent': 'bi-whatsapp',
            'promise_made': 'bi-handshake',
            'promise_missed': 'bi-exclamation-triangle',
            'partial_payment': 'bi-cash',
            'full_payment': 'bi-check-circle-fill',
            'due_date_changed': 'bi-calendar2-event',
            'status_changed': 'bi-arrow-repeat',
            'note_added': 'bi-pencil',
            'escalated': 'bi-alarm',
            'disputed': 'bi-x-circle',
        }
        return icons.get(self.activity_type, 'bi-circle')

    @property
    def badge_class(self):
        classes = {
            'full_payment': 'success',
            'partial_payment': 'success',
            'promise_made': 'info',
            'promise_missed': 'warning',
            'reminder_sent': 'primary',
            'disputed': 'danger',
            'escalated': 'danger',
        }
        return classes.get(self.activity_type, 'secondary')
