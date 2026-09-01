from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from products.models import Product

from website_cms.models import (
    FAQ,
    BlogPost,
    ContactLead,
    HomePageHero,
    HomeStat,
    Project,
    Service,
    SiteSettings,
    Testimonial,
)

User = get_user_model()


class WebsiteCMSTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin@mildadata.com",
            email="admin@mildadata.com",
            password="adminpassword123",
        )
        self.normal_user = User.objects.create_user(
            username="user@mildadata.com",
            email="user@mildadata.com",
            password="userpassword123",
        )

        # Seed test CMS objects
        self.hero = HomePageHero.objects.create(
            heading="Build Digital Products That Matter",
            description="Enterprise SaaS tools and regional AI solutions.",
        )
        self.service = Service.objects.create(
            name="Custom SaaS Development",
            slug="custom-saas",
            short_description="High performance SaaS systems.",
            full_description="<p>Full service description.</p>",
            status="active",
        )
        self.project = Project.objects.create(
            title="Udhaar B2B Ledger",
            slug="udhaar-ledger",
            short_description="B2B payment collections platform.",
            status="published",
        )
        self.post = BlogPost.objects.create(
            title="SaaS Architecture Best Practices",
            slug="saas-best-practices",
            excerpt="Key practices for SaaS developers.",
            content="<p>Detailed article content.</p>",
            status="published",
        )

    def test_public_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_public_services(self):
        response = self.client.get(reverse("website_cms:services_index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Custom SaaS Development")

        response = self.client.get(reverse("website_cms:service_detail", kwargs={"slug": "custom-saas"}))
        self.assertEqual(response.status_code, 200)

    def test_public_projects(self):
        response = self.client.get(reverse("website_cms:projects_index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Udhaar B2B Ledger")

    def test_public_blog(self):
        response = self.client.get(reverse("website_cms:blog_index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SaaS Architecture Best Practices")

    def test_public_contact_submission(self):
        response = self.client.post(
            reverse("website_cms:contact"),
            {
                "name": "Jane Tester",
                "email": "jane@example.com",
                "phone": "+91 99999 88888",
                "company": "Test Co",
                "message": "Interested in Fleet Management OS demo.",
                "product_or_service": "Fleet Management",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ContactLead.objects.filter(email="jane@example.com").exists())

    def test_admin_dashboard_unauthorized(self):
        response = self.client.get(reverse("website_cms:dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirects to /admin/login/

    def test_admin_dashboard_authorized(self):
        self.client.login(username="admin@mildadata.com", password="adminpassword123")
        response = self.client.get(reverse("website_cms:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Executive Dashboard")

    def test_dedicated_admin_login(self):
        # GET login page
        response = self.client.get(reverse("website_cms:admin_login"))
        self.assertEqual(response.status_code, 200)

        # POST valid admin credentials
        response = self.client.post(
            reverse("website_cms:admin_login"),
            {"username": "admin@mildadata.com", "password": "adminpassword123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/admin/dashboard/")

        # POST normal non-admin user credentials
        self.client.logout()
        response = self.client.post(
            reverse("website_cms:admin_login"),
            {"username": "user@mildadata.com", "password": "userpassword123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access Denied")

    def test_admin_homepage_cms_update(self):
        self.client.login(username="admin@mildadata.com", password="adminpassword123")
        response = self.client.post(
            reverse("website_cms:homepage_admin"),
            {
                "action": "update_hero",
                "badge": "UPDATED BADGE",
                "heading": "New Hero Heading",
                "subheading": "New Subheading",
                "description": "New Description",
                "primary_cta": "Explore",
                "primary_cta_url": "/products/",
                "secondary_cta": "Contact",
                "secondary_cta_url": "/contact/",
                "is_visible": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.heading, "New Hero Heading")
