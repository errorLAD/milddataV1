from django.db import models
from django.utils import timezone
from core.models import TenantModel

class Udhaar(TenantModel):
    STATUS_CHOICES = (
        ('Due', 'Due'),
        ('Overdue', 'Overdue'),
        ('Payment Promised', 'Payment Promised'),
        ('Partially Paid', 'Partially Paid'),
        ('Paid', 'Paid'),
        ('Disputed', 'Disputed'),
    )

    VERIFICATION_CHOICES = (
        ('Verified', 'Verified'),
        ('Payment Claimed', 'Payment Claimed'),
        ('Pending Verification', 'Pending Verification'),
        ('Paid', 'Paid'),
    )

    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='udhaars')
    sale = models.ForeignKey('sales.Sale', on_delete=models.SET_NULL, null=True, blank=True, related_name='udhaars')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Original Udhaar Amount")
    late_fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Late Fees Added")
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Due')
    verification_status = models.CharField(max_length=30, choices=VERIFICATION_CHOICES, default='Verified')
    
    promised_date = models.DateField(null=True, blank=True)
    promised_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    promise_broken = models.BooleanField(default=False, verbose_name="Promise Broken Flag")
    
    currency = models.CharField(max_length=10, default='USD')
    currency_symbol = models.CharField(max_length=5, default='$')
    last_reminder_sent = models.DateTimeField(null=True, blank=True)
    next_followup_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.currency_symbol and self.business:
            try:
                from settings_app.models import BusinessSettings
                b_settings, _ = BusinessSettings.objects.get_or_create(business=self.business)
                self.currency = b_settings.currency
                self.currency_symbol = b_settings.currency_symbol
            except Exception:
                pass
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['due_date', '-created_at']

    def __str__(self):
        return f"Udhaar #{self.id} - {self.customer.name} ({self.remaining_amount})"

    @property
    def original_amount(self):
        return self.total_amount

    @property
    def days_overdue(self):
        if self.status == 'Paid' or not self.due_date:
            return 0
        today = timezone.now().date()
        diff = (today - self.due_date).days
        return max(0, diff)

    @property
    def is_overdue(self):
        return self.days_overdue > 0 and self.status != 'Paid'

    def update_status(self):
        if self.remaining_amount <= 0:
            self.status = 'Paid'
            self.remaining_amount = 0
            self.verification_status = 'Paid'
        elif self.paid_amount > 0 and self.remaining_amount > 0:
            if self.is_overdue:
                self.status = 'Overdue'
            else:
                self.status = 'Partially Paid'
        elif self.is_overdue:
            self.status = 'Overdue'
        self.save()
