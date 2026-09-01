from django.db import models
from core.models import TenantModel

class Notification(TenantModel):
    CATEGORY_CHOICES = (
        ('Overdue', 'Overdue Payment'),
        ('Udhaar Due Today', 'Udhaar Due Today'),
        ('Payment Received', 'Payment Received'),
        ('Promise', 'Payment Promised'),
        ('Dispute', 'Disputed Balance'),
        ('Low Stock', 'Low Inventory Stock'),
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Overdue')
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.category}] {self.title}"
