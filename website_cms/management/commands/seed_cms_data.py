from django.core.management.base import BaseCommand
from website_cms.models import (
    FAQ,
    BlogCategory,
    BlogPost,
    FooterConfig,
    HomePageHero,
    HomeStat,
    HomeWhyChoose,
    LegalPage,
    NavigationItem,
    Project,
    SEOSetting,
    Service,
    SiteSettings,
    TeamMember,
    Testimonial,
)


class Command(BaseCommand):
    help = "Seed initial Milda Data CMS content (Site Settings, Hero, Stats, Services, FAQs, Blog)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Milda Data CMS default records...")

        # 0. Ensure Admin Superuser
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "ab.mishra@yahoo.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.email = "ab.mishra@yahoo.com"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password("Admin@1234")
        admin_user.save()
        self.stdout.write(self.style.SUCCESS("Admin Superuser configured: admin / ab.mishra@yahoo.com"))

        # 1. Site Settings
        settings_obj = SiteSettings.get_settings()
        settings_obj.company_name = "Milda Data"
        settings_obj.contact_email = "ab.mishra@yahoo.com"
        settings_obj.phone_number = "+91 98765 43210"
        settings_obj.tagline = "Enterprise Cloud SaaS Applications & AI Data Platform"
        settings_obj.save()

        # 2. Homepage Hero
        hero = HomePageHero.objects.first() or HomePageHero.objects.create()
        hero.badge = "NEXT-GEN ENTERPRISE SAAS & AI PLATFORM"
        hero.heading = "Build & Run Digital Products That Matter"
        hero.subheading = "We design, engineer, and deploy high-performance SaaS products and AI data solutions."
        hero.description = "Automate financial ledgers, heavy machinery fleets, property portfolios, inventory purchasing, and regional language AI model training on a single unified platform."
        hero.primary_cta = "Explore SaaS Products"
        hero.primary_cta_url = "/products/"
        hero.secondary_cta = "Contact Sales"
        hero.secondary_cta_url = "/contact/"
        hero.save()

        # 3. Stats
        if not HomeStat.objects.exists():
            HomeStat.objects.create(number="10+", label="Products", icon="🚀", sort_order=1)
            HomeStat.objects.create(number="5+", label="Industries", icon="🏬", sort_order=2)
            HomeStat.objects.create(number="50+", label="Features", icon="⚡", sort_order=3)
            HomeStat.objects.create(number="99.9%", label="Uptime SLA", icon="🛡️", sort_order=4)

        # 4. Why Milda Data
        if not HomeWhyChoose.objects.exists():
            HomeWhyChoose.objects.create(
                heading="Enterprise Cloud Infrastructure",
                description="Secure 256-bit SSL encrypted cloud platform with high availability and zero setup friction.",
                icon="☁️",
                sort_order=1,
            )
            HomeWhyChoose.objects.create(
                heading="Regional AI & Data Studio",
                description="Specialized audio transcription, text annotation, and trilingual dataset curation for Indic AI models.",
                icon="🧠",
                sort_order=2,
            )
            HomeWhyChoose.objects.create(
                heading="Instant 5-Minute Onboarding",
                description="Launch production-ready SaaS tools with guest mode preview and no credit card required.",
                icon="⚡",
                sort_order=3,
            )

        # 5. Default Services
        if not Service.objects.exists():
            Service.objects.create(
                name="SaaS Product Engineering",
                slug="saas-development",
                short_description="End-to-end multi-tenant SaaS architecture, billing integration, and role-based controls.",
                full_description="<p>We build production-ready enterprise SaaS products designed for high scale and seamless user adoption.</p>",
                icon="💻",
                status="active",
                sort_order=1,
            )
            Service.objects.create(
                name="AI Dataset & Model Training",
                slug="ai-data-solutions",
                short_description="High-accuracy Indic regional language speech transcription, text labeling, and dataset curation.",
                full_description="<p>Custom AI dataset labeling and machine learning pipeline optimization.</p>",
                icon="🤖",
                status="active",
                sort_order=2,
            )
            Service.objects.create(
                name="Workflow & Logistics Automation",
                slug="automation",
                short_description="GPS fleet tracking, heavy machinery hour logs, property rent collection, and B2B payment automation.",
                full_description="<p>Automate operational bottlenecks across logistics, heavy machinery, and real estate portfolios.</p>",
                icon="⚙️",
                status="active",
                sort_order=3,
            )

        # 6. Default Blog Categories & Post
        cat, _ = BlogCategory.objects.get_or_create(name="Engineering & Cloud", slug="engineering")
        if not BlogPost.objects.exists():
            BlogPost.objects.create(
                title="Building Multi-Tenant SaaS Systems with Django & Regional Currency Engine",
                slug="multi-tenant-saas-django",
                category=cat,
                excerpt="How Milda Data handles regional currency auto-detection, GST/VAT calculations, and guest trial access.",
                content="<p>Architecting enterprise SaaS platforms requires robust billing models, regional tax compliance, and seamless user onboarding.</p>",
                author_name="Milda Data Engineering Team",
                status="published",
                reading_time="6 min read",
            )

        # 7. FAQs
        if not FAQ.objects.exists():
            FAQ.objects.create(
                question="What SaaS products are included in the Milda Data Marketplace?",
                answer="Our platform includes B2B Payment Reminder (Udhaar), Supplier Onboarding OS, Business SaaS Lite, Fleet Management OS, StockFlow (Inventory & Purchasing), MachineOS (Heavy Machinery), and PropFlow (Property Management).",
                placement="homepage",
                sort_order=1,
            )
            FAQ.objects.create(
                question="Can I manage all website content through the Admin CMS?",
                answer="Yes! The Milda Data CMS allows authorized administrators to edit the homepage hero, products, services, projects, blog articles, leads, media, navigation, and SEO settings without modifying code.",
                placement="global",
                sort_order=2,
            )

        # 8. Navigation & Footer
        if not NavigationItem.objects.exists():
            NavigationItem.objects.create(label="Data Labeling", url="/labeling/", sort_order=1)
            NavigationItem.objects.create(label="SAAS STORE", url="/products/", sort_order=2)
            NavigationItem.objects.create(label="Blog", url="/blog/", sort_order=3)
            NavigationItem.objects.create(label="Contact", url="/contact/", sort_order=4)

        footer = FooterConfig.get_config()
        footer.contact_email = "ab.mishra@yahoo.com"
        footer.save()

        self.stdout.write(self.style.SUCCESS("Milda Data CMS seed completed successfully!"))
