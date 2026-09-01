from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from products.models import Order, Product
from products.saas_registry import SAAS_PRODUCTS, get_all_saas_products

User = get_user_model()


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class SaaSDirectoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
        )
        self.product = Product.objects.create(
            name="Payment Reminder / B2B Payment",
            description="Test description",
            category="saas_tool",
            price_inr_monthly=Decimal("199.00"),
            price_inr_yearly=Decimal("1982.00"),
            price_usd_monthly=Decimal("5.00"),
            price_usd_yearly=Decimal("49.80"),
            gst_tax_rate=Decimal("18.00"),
            vat_tax_rate=Decimal("0.00"),
            is_active=True,
        )

    def test_catalog_view(self):
        response = self.client.get(reverse("products:catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/catalog.html")

    def test_saas_directory_view(self):
        response = self.client.get(reverse("products:saas_directory"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/saas_directory.html")

    def test_regional_pricing_rules(self):
        # India + Monthly
        sub_in_m, tax_in_m, tot_in_m, rate_in_m = self.product.get_tax_breakdown(currency="INR", billing_cycle="monthly")
        self.assertEqual(sub_in_m, Decimal("199.00"))
        self.assertEqual(self.product.get_display_price("INR", "monthly"), "₹199/mo")

        # India + Yearly (17% discount)
        sub_in_y, tax_in_y, tot_in_y, rate_in_y = self.product.get_tax_breakdown(currency="INR", billing_cycle="yearly")
        self.assertEqual(sub_in_y, Decimal("1982.00"))
        self.assertIn("Save 17%", self.product.get_display_price("INR", "yearly"))

        # International + Monthly
        sub_int_m, tax_int_m, tot_int_m, rate_int_m = self.product.get_tax_breakdown(currency="USD", billing_cycle="monthly")
        self.assertEqual(sub_int_m, Decimal("5.00"))
        self.assertEqual(self.product.get_display_price("USD", "monthly"), "$5/mo")

        # International + Yearly (17% discount)
        sub_int_y, tax_int_y, tot_int_y, rate_int_y = self.product.get_tax_breakdown(currency="USD", billing_cycle="yearly")
        self.assertEqual(sub_int_y, Decimal("49.80"))
        self.assertIn("Save 17%", self.product.get_display_price("USD", "yearly"))

    def test_saas_registry_regional_cards(self):
        # Test International + Monthly
        products_usd = get_all_saas_products(currency="USD", billing_cycle="monthly")
        for p in products_usd:
            self.assertEqual(p["display_price"], "$5/mo")
            self.assertEqual(p["price_amount"], 5.00)

        # Test India + Monthly
        products_inr = get_all_saas_products(currency="INR", billing_cycle="monthly")
        for p in products_inr:
            self.assertEqual(p["display_price"], "₹199/mo")
            self.assertEqual(p["price_amount"], 199.00)

        # Test International + Yearly
        products_usd_yr = get_all_saas_products(currency="USD", billing_cycle="yearly")
        for p in products_usd_yr:
            self.assertEqual(p["display_price"], "$49.80/yr (Save 17%)")
            self.assertEqual(p["price_amount"], 49.80)

    def test_region_middleware_switching(self):
        # Switch to International
        response = self.client.get(reverse("products:saas_directory"), {"region": "INT", "currency": "USD"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get("region"), "INT")
        self.assertEqual(self.client.session.get("currency"), "USD")
        self.assertContains(response, "$5/mo")
        self.assertNotContains(response, "₹199/mo")

        # Switch to India
        response_in = self.client.get(reverse("products:saas_directory"), {"region": "IN", "currency": "INR"})
        self.assertEqual(response_in.status_code, 200)
        self.assertEqual(self.client.session.get("region"), "IN")
        self.assertEqual(self.client.session.get("currency"), "INR")
        self.assertContains(response_in, "₹199/mo")

    @patch("products.views._is_url_reachable", return_value=True)
    def test_saas_launch_guest(self, mock_reachable):
        self.client.get(reverse("accounts:guest_login"))
        for slug, item in SAAS_PRODUCTS.items():
            url = reverse("products:saas_launch", kwargs={"slug": slug})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(item["default_url"]))

    @patch("products.views._is_url_reachable", return_value=True)
    def test_saas_launch_authenticated(self, mock_reachable):
        self.client.login(username="testuser", password="testpassword123")
        for slug, item in SAAS_PRODUCTS.items():
            url = reverse("products:saas_launch", kwargs={"slug": slug})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(item["default_url"]))
