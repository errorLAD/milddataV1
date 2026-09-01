from django.db import models


class QuoteRequest(models.Model):
    DATA_TYPE_CHOICES = [
        ("audio_transcription", "Audio Transcription"),
        ("text_annotation", "Text Annotation"),
        ("trilingual_dataset", "Trilingual Dataset"),
        ("image_annotation", "Image Annotation"),
        ("other", "Other"),
    ]

    company_name = models.CharField(max_length=200)
    email = models.EmailField()
    data_type = models.CharField(max_length=50, choices=DATA_TYPE_CHOICES)
    volume = models.CharField(
        max_length=100,
        help_text="e.g. 500 hours, 10K sentences",
    )
    timeline = models.CharField(
        max_length=100,
        help_text="e.g. 4 weeks, ASAP",
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Quote Request"
        verbose_name_plural = "Quote Requests"

    def __str__(self):
        return f"{self.company_name} — {self.get_data_type_display()}"
