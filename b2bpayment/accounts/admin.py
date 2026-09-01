from django.contrib import admin
from .models import Business, UserProfile

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner_name', 'phone', 'email', 'created_at')
    search_fields = ('name', 'owner_name', 'phone', 'email')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'business', 'role', 'phone')
    list_filter = ('role', 'business')
    search_fields = ('user__username', 'business__name', 'phone')
