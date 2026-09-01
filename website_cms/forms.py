from django import forms
from products.models import Product

from .models import (
    FAQ,
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
from .utils import sanitize_html


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = "__all__"
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "tagline": forms.TextInput(attrs={"class": "form-control"}),
            "logo_url": forms.URLInput(attrs={"class": "form-control"}),
            "default_language": forms.TextInput(attrs={"class": "form-control"}),
            "default_currency": forms.TextInput(attrs={"class": "form-control"}),
            "contact_email": forms.EmailInput(attrs={"class": "form-control"}),
            "support_email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "business_hours": forms.TextInput(attrs={"class": "form-control"}),
            "social_linkedin": forms.URLInput(attrs={"class": "form-control"}),
            "social_twitter": forms.URLInput(attrs={"class": "form-control"}),
            "social_github": forms.URLInput(attrs={"class": "form-control"}),
            "google_analytics_id": forms.TextInput(attrs={"class": "form-control"}),
            "default_cta_title": forms.TextInput(attrs={"class": "form-control"}),
            "default_cta_subtitle": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "default_cta_button_text": forms.TextInput(attrs={"class": "form-control"}),
            "default_cta_button_url": forms.TextInput(attrs={"class": "form-control"}),
        }


class HomePageHeroForm(forms.ModelForm):
    class Meta:
        model = HomePageHero
        fields = "__all__"
        widgets = {
            "badge": forms.TextInput(attrs={"class": "form-control"}),
            "heading": forms.TextInput(attrs={"class": "form-control"}),
            "subheading": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "hero_image_url": forms.URLInput(attrs={"class": "form-control"}),
            "hero_video_url": forms.URLInput(attrs={"class": "form-control"}),
            "primary_cta": forms.TextInput(attrs={"class": "form-control"}),
            "primary_cta_url": forms.TextInput(attrs={"class": "form-control"}),
            "secondary_cta": forms.TextInput(attrs={"class": "form-control"}),
            "secondary_cta_url": forms.TextInput(attrs={"class": "form-control"}),
        }


class HomeStatForm(forms.ModelForm):
    class Meta:
        model = HomeStat
        fields = "__all__"
        widgets = {
            "number": forms.TextInput(attrs={"class": "form-control"}),
            "label": forms.TextInput(attrs={"class": "form-control"}),
            "icon": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class HomeWhyChooseForm(forms.ModelForm):
    class Meta:
        model = HomeWhyChoose
        fields = "__all__"
        widgets = {
            "heading": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "icon": forms.TextInput(attrs={"class": "form-control"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "short_description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "full_description": forms.Textarea(attrs={"class": "form-control richtext-editor", "rows": 8}),
            "icon": forms.TextInput(attrs={"class": "form-control"}),
            "hero_image_url": forms.URLInput(attrs={"class": "form-control"}),
            "features": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "One feature per line"}),
            "benefits": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "One benefit per line"}),
            "process_steps": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Step 1: Requirement analysis..."}),
            "technologies": forms.TextInput(attrs={"class": "form-control", "placeholder": "Python, Django, React"}),
            "pricing_info": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
            "seo_title": forms.TextInput(attrs={"class": "form-control"}),
            "meta_description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean_full_description(self):
        content = self.cleaned_data.get("full_description", "")
        return sanitize_html(content)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = "__all__"
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "client_name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "short_description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "challenge": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "solution": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "results": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "features": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "technologies": forms.TextInput(attrs={"class": "form-control"}),
            "featured_image_url": forms.URLInput(attrs={"class": "form-control"}),
            "video_url": forms.URLInput(attrs={"class": "form-control"}),
            "website_url": forms.URLInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
            "seo_title": forms.TextInput(attrs={"class": "form-control"}),
            "meta_description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class BlogCategoryForm(forms.ModelForm):
    class Meta:
        model = BlogCategory
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = "__all__"
        exclude = ["views_count", "preview_token"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "excerpt": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "content": forms.Textarea(attrs={"class": "form-control richtext-editor", "rows": 10}),
            "featured_image_url": forms.URLInput(attrs={"class": "form-control"}),
            "author_name": forms.TextInput(attrs={"class": "form-control"}),
            "reading_time": forms.TextInput(attrs={"class": "form-control"}),
            "tags": forms.TextInput(attrs={"class": "form-control", "placeholder": "AI, SaaS, Cloud"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "publish_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "seo_title": forms.TextInput(attrs={"class": "form-control"}),
            "meta_description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "og_image_url": forms.URLInput(attrs={"class": "form-control"}),
        }

    def clean_content(self):
        content = self.cleaned_data.get("content", "")
        return sanitize_html(content)


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "photo_url": forms.URLInput(attrs={"class": "form-control"}),
            "public_email": forms.EmailInput(attrs={"class": "form-control"}),
            "linkedin_url": forms.URLInput(attrs={"class": "form-control"}),
            "twitter_url": forms.URLInput(attrs={"class": "form-control"}),
            "github_url": forms.URLInput(attrs={"class": "form-control"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = "__all__"
        widgets = {
            "customer_name": forms.TextInput(attrs={"class": "form-control"}),
            "company": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.TextInput(attrs={"class": "form-control"}),
            "photo_url": forms.URLInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "rating": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 5}),
            "product_name": forms.TextInput(attrs={"class": "form-control"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = "__all__"
        widgets = {
            "question": forms.TextInput(attrs={"class": "form-control"}),
            "answer": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "placement": forms.Select(attrs={"class": "form-select"}),
            "product_name": forms.TextInput(attrs={"class": "form-control"}),
            "service_name": forms.TextInput(attrs={"class": "form-control"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def clean_answer(self):
        answer = self.cleaned_data.get("answer", "")
        return sanitize_html(answer)


class ContactLeadForm(forms.ModelForm):
    class Meta:
        model = ContactLead
        fields = "__all__"
        widgets = {
            "lead_type": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "company": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "product_or_service": forms.TextInput(attrs={"class": "form-control"}),
            "preferred_date_time": forms.TextInput(attrs={"class": "form-control"}),
            "source_page": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "internal_notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "follow_up_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "assigned_staff": forms.TextInput(attrs={"class": "form-control"}),
        }


class NewsletterSubscriberForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email", "source", "is_active"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter your business email"}),
            "source": forms.TextInput(attrs={"class": "form-control"}),
        }


class NavigationItemForm(forms.ModelForm):
    class Meta:
        model = NavigationItem
        fields = "__all__"
        widgets = {
            "label": forms.TextInput(attrs={"class": "form-control"}),
            "url": forms.TextInput(attrs={"class": "form-control"}),
            "icon": forms.TextInput(attrs={"class": "form-control"}),
            "parent": forms.Select(attrs={"class": "form-select"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class FooterConfigForm(forms.ModelForm):
    class Meta:
        model = FooterConfig
        fields = "__all__"
        widgets = {
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "copyright_text": forms.TextInput(attrs={"class": "form-control"}),
            "address_display": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "contact_email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_display": forms.TextInput(attrs={"class": "form-control"}),
        }


class MediaAssetForm(forms.ModelForm):
    class Meta:
        model = MediaAsset
        fields = ["title", "file", "media_type", "alt_text", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "file": forms.FileInput(attrs={"class": "form-control"}),
            "media_type": forms.Select(attrs={"class": "form-select"}),
            "alt_text": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            # Validate max file size (e.g. 25MB)
            if file.size > 25 * 1024 * 1024:
                raise forms.ValidationError("File size exceeds maximum allowed limit of 25MB.")
            ext = file.name.split(".")[-1].lower()
            allowed_exts = ["jpg", "jpeg", "png", "gif", "svg", "webp", "mp4", "webm", "pdf", "zip"]
            if ext not in allowed_exts:
                raise forms.ValidationError(f"File extension .{ext} is not allowed.")
        return file


class SEOSettingForm(forms.ModelForm):
    class Meta:
        model = SEOSetting
        fields = "__all__"
        widgets = {
            "page_identifier": forms.Select(attrs={"class": "form-select"}),
            "site_title": forms.TextInput(attrs={"class": "form-control"}),
            "meta_description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "keywords": forms.TextInput(attrs={"class": "form-control"}),
            "og_image_url": forms.URLInput(attrs={"class": "form-control"}),
            "robots_directive": forms.TextInput(attrs={"class": "form-control"}),
        }


class LegalPageForm(forms.ModelForm):
    class Meta:
        model = LegalPage
        fields = "__all__"
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control richtext-editor", "rows": 10}),
            "version": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_content(self):
        content = self.cleaned_data.get("content", "")
        return sanitize_html(content)


class UserPermissionRoleForm(forms.ModelForm):
    class Meta:
        model = UserPermissionRole
        fields = "__all__"
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
            "role": forms.Select(attrs={"class": "form-select"}),
        }


class ProductCMSForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "features": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "billing_type": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "price_usd": forms.NumberInput(attrs={"class": "form-control"}),
            "price_inr_monthly": forms.NumberInput(attrs={"class": "form-control"}),
            "price_inr_yearly": forms.NumberInput(attrs={"class": "form-control"}),
            "price_usd_monthly": forms.NumberInput(attrs={"class": "form-control"}),
            "price_usd_yearly": forms.NumberInput(attrs={"class": "form-control"}),
            "gst_tax_rate": forms.NumberInput(attrs={"class": "form-control"}),
            "vat_tax_rate": forms.NumberInput(attrs={"class": "form-control"}),
            "access_info": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
