from django.contrib import admin
from .models import (
    FAQ,
    AuditLog,
    BlogCategory,
    BlogPost,
    ContactLead,
    FooterConfig,
    HomePageHero,
    HomeStat,
    HomeWhyChoose,
    LegalPage,
    MediaAsset,
    NavigationItem,
    NewsletterSubscriber,
    Project,
    SEOSetting,
    Service,
    SiteSettings,
    TeamMember,
    Testimonial,
    UserPermissionRole,
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ["company_name", "contact_email", "phone_number", "updated_at"]


@admin.register(HomePageHero)
class HomePageHeroAdmin(admin.ModelAdmin):
    list_display = ["heading", "badge", "is_visible", "updated_at"]


@admin.register(HomeStat)
class HomeStatAdmin(admin.ModelAdmin):
    list_display = ["number", "label", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]


@admin.register(HomeWhyChoose)
class HomeWhyChooseAdmin(admin.ModelAdmin):
    list_display = ["heading", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "status", "sort_order", "created_at"]
    list_filter = ["status"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["sort_order", "status"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "client_name", "category", "is_featured", "status", "sort_order"]
    list_filter = ["status", "is_featured"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "author_name", "status", "publish_date", "views_count"]
    list_filter = ["status", "category"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ["name", "role", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ["customer_name", "company", "rating", "is_approved", "is_featured"]
    list_filter = ["is_approved", "is_featured"]


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ["question", "category", "placement", "sort_order", "is_active"]
    list_filter = ["placement", "is_active"]


@admin.register(ContactLead)
class ContactLeadAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "lead_type", "company", "status", "created_at"]
    list_filter = ["lead_type", "status"]


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "is_active", "source", "created_at"]


@admin.register(NavigationItem)
class NavigationItemAdmin(admin.ModelAdmin):
    list_display = ["label", "url", "parent", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]


@admin.register(FooterConfig)
class FooterConfigAdmin(admin.ModelAdmin):
    list_display = ["copyright_text", "contact_email", "updated_at"]


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ["title", "media_type", "upload_date"]
    list_filter = ["media_type"]


@admin.register(SEOSetting)
class SEOSettingAdmin(admin.ModelAdmin):
    list_display = ["page_identifier", "site_title", "updated_at"]


@admin.register(LegalPage)
class LegalPageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "version", "is_published"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "user_email", "action", "target_model", "ip_address"]
    readonly_fields = ["user", "user_email", "action", "target_model", "target_id", "details", "ip_address", "timestamp"]


@admin.register(UserPermissionRole)
class UserPermissionRoleAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "can_publish", "can_delete", "can_manage_settings"]
