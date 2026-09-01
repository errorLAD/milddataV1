import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class SiteSettings(models.Model):
    company_name = models.CharField(max_length=200, default="Milda Data")
    tagline = models.CharField(max_length=300, default="Enterprise SaaS Applications & Regional Language AI Tools")
    logo = models.ImageField(upload_to="cms/settings/", blank=True, null=True)
    logo_url = models.URLField(max_length=500, blank=True, default="https://i.postimg.cc/43gxKLrL/6e2fd4bb-c219-46d7-a5a3-21d4df5b9461.png")
    favicon = models.ImageField(upload_to="cms/settings/", blank=True, null=True)
    default_language = models.CharField(max_length=20, default="en")
    default_currency = models.CharField(max_length=10, default="INR")
    contact_email = models.EmailField(default="ab.mishra@yahoo.com")
    support_email = models.EmailField(default="support@mildadata.com")
    phone_number = models.CharField(max_length=50, blank=True, default="")
    address = models.TextField(blank=True, default="Milda Data Enterprise HQ, Tech Hub, India")
    business_hours = models.CharField(max_length=200, default="Mon - Fri: 9:00 AM - 6:00 PM IST")
    social_linkedin = models.URLField(blank=True, default="https://linkedin.com")
    social_twitter = models.URLField(blank=True, default="https://twitter.com")
    social_github = models.URLField(blank=True, default="https://github.com")
    google_analytics_id = models.CharField(max_length=50, blank=True, help_text="e.g. G-XXXXXXXXXX")
    default_cta_title = models.CharField(max_length=200, default="Ready to Automate Your Business?")
    default_cta_subtitle = models.TextField(default="Deploy our enterprise SaaS tools in under 5 minutes with zero setup friction.")
    default_cta_button_text = models.CharField(max_length=100, default="Explore SaaS Catalog")
    default_cta_button_url = models.CharField(max_length=300, default="/products/")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return f"Site Settings ({self.company_name})"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HomePageHero(models.Model):
    badge = models.CharField(max_length=100, default="NEXT-GEN ENTERPRISE SAAS & AI")
    heading = models.CharField(max_length=250, default="Build & Run Digital Products That Matter")
    subheading = models.CharField(max_length=300, default="We design, engineer, and deploy high-performance SaaS products and AI data solutions.")
    description = models.TextField(default="Automate financial ledgers, heavy machinery fleets, property portfolios, inventory purchasing, and regional language AI model training on a single unified platform.")
    hero_image = models.ImageField(upload_to="cms/homepage/", blank=True, null=True)
    hero_image_url = models.URLField(max_length=500, blank=True)
    hero_video_url = models.URLField(max_length=500, blank=True, help_text="YouTube, Vimeo or MP4 URL")
    primary_cta = models.CharField(max_length=100, default="Explore Products")
    primary_cta_url = models.CharField(max_length=300, default="/products/")
    secondary_cta = models.CharField(max_length=100, default="Book Live Demo")
    secondary_cta_url = models.CharField(max_length=300, default="/contact/")
    is_visible = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Homepage Hero"
        verbose_name_plural = "Homepage Hero"

    def __str__(self):
        return f"Hero: {self.heading[:40]}"


class HomeStat(models.Model):
    number = models.CharField(max_length=50, default="10+")
    label = models.CharField(max_length=100, default="SaaS Products")
    icon = models.CharField(max_length=50, default="🚀", help_text="Emoji or Icon class")
    description = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.number} - {self.label}"


class HomeWhyChoose(models.Model):
    heading = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=50, default="⚡")
    image = models.ImageField(upload_to="cms/why/", blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.heading


class Service(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    short_description = models.TextField(help_text="Shown on service cards")
    full_description = models.TextField(help_text="HTML / Rich Text full service details")
    icon = models.CharField(max_length=50, default="🛠️")
    hero_image = models.ImageField(upload_to="cms/services/", blank=True, null=True)
    hero_image_url = models.URLField(max_length=500, blank=True)
    features = models.TextField(blank=True, help_text="One feature per line")
    benefits = models.TextField(blank=True, help_text="One benefit per line")
    process_steps = models.TextField(blank=True, help_text="Step 1: Description (one per line)")
    technologies = models.CharField(max_length=300, blank=True, help_text="Comma-separated e.g. Python, Django, PyTorch, PostgreSQL")
    pricing_info = models.CharField(max_length=200, blank=True, help_text="e.g. Custom Quote / Starting from $499")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    sort_order = models.PositiveIntegerField(default=0)
    seo_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_features_list(self):
        return [f.strip() for f in self.features.splitlines() if f.strip()]

    def get_benefits_list(self):
        return [b.strip() for b in self.benefits.splitlines() if b.strip()]

    def get_process_list(self):
        return [p.strip() for p in self.process_steps.splitlines() if p.strip()]

    def get_technologies_list(self):
        return [t.strip() for t in self.technologies.split(",") if t.strip()]


class Project(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    client_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=100, default="Enterprise Software")
    short_description = models.TextField()
    challenge = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    results = models.TextField(blank=True)
    features = models.TextField(blank=True, help_text="One feature per line")
    technologies = models.CharField(max_length=300, blank=True, help_text="Comma-separated")
    featured_image = models.ImageField(upload_to="cms/projects/", blank=True, null=True)
    featured_image_url = models.URLField(max_length=500, blank=True)
    video_url = models.URLField(max_length=500, blank=True)
    website_url = models.URLField(max_length=500, blank=True)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="published")
    sort_order = models.PositiveIntegerField(default=0)
    seo_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_features_list(self):
        return [f.strip() for f in self.features.splitlines() if f.strip()]

    def get_technologies_list(self):
        return [t.strip() for t in self.technologies.split(",") if t.strip()]


class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Blog Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=270, unique=True, blank=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    excerpt = models.TextField(help_text="Short summary for article cards")
    content = models.TextField(help_text="Full article body (Rich Text / HTML)")
    featured_image = models.ImageField(upload_to="cms/blog/", blank=True, null=True)
    featured_image_url = models.URLField(max_length=500, blank=True)
    author_name = models.CharField(max_length=100, default="Milda Data Editorial Team")
    reading_time = models.CharField(max_length=50, default="5 min read")
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="published")
    publish_date = models.DateTimeField(default=timezone.now)
    views_count = models.PositiveIntegerField(default=0)
    preview_token = models.CharField(max_length=64, blank=True, default=uuid.uuid4)
    seo_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    og_image_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publish_date", "-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.preview_token:
            self.preview_token = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def get_tags_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class TeamMember(models.Model):
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=150)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="cms/team/", blank=True, null=True)
    photo_url = models.URLField(max_length=500, blank=True)
    public_email = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.name} — {self.role}"


class Testimonial(models.Model):
    customer_name = models.CharField(max_length=150)
    company = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=150, blank=True)
    photo = models.ImageField(upload_to="cms/testimonials/", blank=True, null=True)
    photo_url = models.URLField(max_length=500, blank=True)
    content = models.TextField()
    rating = models.PositiveIntegerField(default=5, help_text="1 to 5 stars")
    product_name = models.CharField(max_length=200, blank=True, help_text="Product or Service associated")
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "-id"]

    def __str__(self):
        return f"{self.customer_name} ({self.company or 'Client'})"


class FAQ(models.Model):
    PLACEMENT_CHOICES = [
        ("global", "Global / All Pages"),
        ("homepage", "Homepage Only"),
        ("product", "Product Pages"),
        ("service", "Service Pages"),
        ("contact", "Contact Page"),
    ]

    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=100, default="General")
    placement = models.CharField(max_length=20, choices=PLACEMENT_CHOICES, default="global")
    product_name = models.CharField(max_length=200, blank=True)
    service_name = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class ContactLead(models.Model):
    LEAD_TYPE_CHOICES = [
        ("contact", "General Contact"),
        ("demo", "Demo Request"),
        ("trial", "Free Trial Request"),
    ]
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified"),
        ("converted", "Converted"),
        ("closed", "Closed"),
        ("spam", "Spam"),
    ]

    lead_type = models.CharField(max_length=20, choices=LEAD_TYPE_CHOICES, default="contact")
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    product_or_service = models.CharField(max_length=200, blank=True)
    preferred_date_time = models.CharField(max_length=100, blank=True)
    source_page = models.CharField(max_length=200, default="Website")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    internal_notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    assigned_staff = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_lead_type_display()}] {self.name} ({self.email}) — {self.status}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=100, default="Website Footer")
    unsubscribe_token = models.CharField(max_length=64, blank=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.unsubscribe_token:
            self.unsubscribe_token = str(uuid.uuid4())
        super().save(*args, **kwargs)


class NavigationItem(models.Model):
    label = models.CharField(max_length=100)
    url = models.CharField(max_length=300, help_text="e.g. /products/ or https://...")
    icon = models.CharField(max_length=50, blank=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    sort_order = models.PositiveIntegerField(default=0)
    open_in_new_tab = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.label} -> {self.label}"
        return self.label


class FooterConfig(models.Model):
    description = models.TextField(default="Milda Data is an enterprise cloud SaaS and regional language AI technology provider empowering modern digital operations.")
    copyright_text = models.CharField(max_length=200, default="© 2026 Milda Data Enterprise. All rights reserved.")
    address_display = models.TextField(blank=True, default="Tech Hub, India")
    contact_email = models.EmailField(default="ab.mishra@yahoo.com")
    phone_display = models.CharField(max_length=50, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Footer Configuration"
        verbose_name_plural = "Footer Configuration"

    def __str__(self):
        return "Footer Configuration"

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class MediaAsset(models.Model):
    MEDIA_TYPE_CHOICES = [
        ("image", "Image"),
        ("video", "Video"),
        ("document", "Document"),
    ]

    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="cms/media/")
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, default="image")
    alt_text = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True)
    file_size_bytes = models.PositiveIntegerField(default=0)
    dimensions = models.CharField(max_length=50, blank=True, help_text="e.g. 1920x1080")
    upload_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-upload_date"]

    def __str__(self):
        return self.title

    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return ""


class SEOSetting(models.Model):
    PAGE_CHOICES = [
        ("homepage", "Homepage"),
        ("products", "Products Catalog"),
        ("services", "Services Directory"),
        ("projects", "Projects Portfolio"),
        ("blog", "Blog Index"),
        ("about", "About Us Page"),
        ("contact", "Contact Us Page"),
    ]

    page_identifier = models.CharField(max_length=50, choices=PAGE_CHOICES, unique=True)
    site_title = models.CharField(max_length=200, help_text="SEO Title Tag")
    meta_description = models.TextField(help_text="Meta Description Tag")
    keywords = models.CharField(max_length=300, blank=True)
    og_image = models.ImageField(upload_to="cms/seo/", blank=True, null=True)
    og_image_url = models.URLField(max_length=500, blank=True)
    robots_directive = models.CharField(max_length=100, default="index, follow")
    include_in_sitemap = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SEO Setting"
        verbose_name_plural = "SEO Settings"

    def __str__(self):
        return f"SEO Settings for {self.get_page_identifier_display()}"


class LegalPage(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    content = models.TextField(help_text="Rich text / HTML legal policy body")
    version = models.CharField(max_length=20, default="1.0")
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    user_email = models.EmailField(blank=True)
    action = models.CharField(max_length=100, help_text="e.g. Product Created, Blog Published, Settings Saved")
    target_model = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.user_email or 'System'} — {self.action}"

    @classmethod
    def log(cls, user, action, target_model, target_id="", details="", ip_address=None):
        email = user.email if user and user.is_authenticated else "Anonymous"
        cls.objects.create(
            user=user if user and user.is_authenticated else None,
            user_email=email,
            action=action,
            target_model=target_model,
            target_id=str(target_id),
            details=details,
            ip_address=ip_address,
        )


class UserPermissionRole(models.Model):
    ROLE_CHOICES = [
        ("super_admin", "Super Admin"),
        ("admin", "Administrator"),
        ("content_manager", "Content Manager"),
        ("product_manager", "Product Manager"),
        ("support", "Support Specialist"),
        ("marketing", "Marketing Lead"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cms_role")
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="admin")
    can_publish = models.BooleanField(default=True)
    can_delete = models.BooleanField(default=True)
    can_manage_settings = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} — {self.get_role_display()}"
