from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from products.models import Product

User = get_user_model()


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class GuestAccessAndSecurityTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Test SaaS Tool",
            description="Test description",
            category="saas_tool",
            price=100.00,
            billing_type="monthly",
            is_active=True,
        )

    def test_guest_login_initializes_session(self):
        response = self.client.get(reverse("accounts:guest_login"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get("is_guest"))
        self.assertTrue(self.client.session.get("guest_id").startswith("guest_"))

    def test_guest_can_access_public_pages(self):
        self.client.get(reverse("accounts:guest_login"))
        
        home_res = self.client.get(reverse("home"))
        self.assertEqual(home_res.status_code, 200)

        catalog_res = self.client.get(reverse("products:catalog"))
        self.assertEqual(catalog_res.status_code, 200)

        saas_res = self.client.get(reverse("products:saas_directory"))
        self.assertEqual(saas_res.status_code, 200)

    def test_guest_restricted_action_enforced_server_side(self):
        self.client.get(reverse("accounts:guest_login"))

        # Guest trying to view admin -> restricted & redirected to login
        admin_res = self.client.get("/admin/dashboard/")
        self.assertEqual(admin_res.status_code, 302)
        self.assertIn(reverse("accounts:login"), admin_res.url)

        # Guest trying to POST purchase -> restricted & redirected to login
        detail_url = reverse("products:detail", kwargs={"pk": self.product.pk})
        purchase_res = self.client.post(detail_url)
        self.assertEqual(purchase_res.status_code, 302)
        self.assertIn(reverse("accounts:login"), purchase_res.url)

    def test_guest_upgrades_to_full_account_on_signup(self):
        self.client.get(reverse("accounts:guest_login"))
        self.assertTrue(self.client.session.get("is_guest"))

        signup_res = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertEqual(signup_res.status_code, 302)
        self.assertFalse(self.client.session.get("is_guest", False))

    def test_security_headers_middleware(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertIn("Content-Security-Policy", response)
