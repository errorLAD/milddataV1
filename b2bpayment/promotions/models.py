from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import TenantModel

class Promotion(TenantModel):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Draft', 'Draft'),
        ('Expired', 'Expired'),
    )

    name = models.CharField(max_length=255, verbose_name="Promotion Name")
    title = models.CharField(max_length=255, verbose_name="Offer Title")
    message = models.TextField(verbose_name="Promotion Message")
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.title})"

    @property
    def is_active(self):
        today = timezone.now().date()
        if self.status == 'Expired':
            return False
        if self.end_date and today > self.end_date:
            return False
        return True

    @property
    def can_upload_more_images(self):
        return self.images.count() < 2

class PromotionImage(TenantModel):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='promotions/posters/')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.pk and self.promotion.images.count() >= 2:
            raise ValidationError("Maximum 2 poster images allowed per promotion. Delete an existing image to upload another.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Poster image for {self.promotion.name}"
