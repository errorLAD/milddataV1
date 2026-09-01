from django.db import models
from core.models import TenantModel

class AIBusinessInsightCache(TenantModel):
    date_range_code = models.CharField(max_length=50, default='30_days', verbose_name="Date Range Filter")
    health_status = models.CharField(max_length=50, default='Needs Attention', verbose_name="Business Health Status")
    health_summary = models.TextField(blank=True, verbose_name="Business Health Summary Text")
    insight_json = models.JSONField(default=dict, verbose_name="Structured AI Insight JSON Payload")
    last_analyzed_at = models.DateTimeField(auto_now=True, verbose_name="Last Analysis Timestamp")

    class Meta:
        unique_together = ['business', 'date_range_code']
        ordering = ['-last_analyzed_at']

    def __str__(self):
        return f"AI Cache ({self.business.name}) - {self.date_range_code}"

class AIAdvisorQueryLog(TenantModel):
    question = models.TextField(verbose_name="User Question")
    answer = models.TextField(verbose_name="AI Advisor Answer")
    asked_at = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")

    class Meta:
        ordering = ['-asked_at']

    def __str__(self):
        return f"Query by {self.business.name}: {self.question[:30]}"
