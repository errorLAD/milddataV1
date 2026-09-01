from django.contrib import admin
from .models import AIBusinessInsightCache, AIAdvisorQueryLog

@admin.register(AIBusinessInsightCache)
class AIBusinessInsightCacheAdmin(admin.ModelAdmin):
    list_display = ('id', 'business', 'date_range_code', 'health_status', 'last_analyzed_at')
    list_filter = ('date_range_code', 'health_status', 'business')

@admin.register(AIAdvisorQueryLog)
class AIAdvisorQueryLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'business', 'question', 'asked_at')
    search_fields = ('question', 'answer')
