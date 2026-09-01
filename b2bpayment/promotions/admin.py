from django.contrib import admin
from .models import Promotion, PromotionImage

class PromotionImageInline(admin.TabularInline):
    model = PromotionImage
    extra = 1

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'business', 'title', 'start_date', 'end_date', 'status', 'created_at')
    list_filter = ('business', 'status', 'start_date', 'end_date')
    search_fields = ('name', 'title', 'message')
    inlines = [PromotionImageInline]

@admin.register(PromotionImage)
class PromotionImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'promotion', 'business', 'created_at')
    list_filter = ('business',)
