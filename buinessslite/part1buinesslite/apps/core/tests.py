from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from apps.core.models import Organization, UserProfile, UserRole
from apps.core.ai_engine import process_ai_request
from apps.inventory.models import Product, ProductCategory, ProductType, StockMovement, MovementType
from apps.sales.models import Customer, Invoice, InvoiceItem, InvoiceStatus, Payment
from apps.finance.models import Expense, ExpenseCategory

class BusinessLiteSystemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testadmin', email='admin@test.com', password='password123')
        self.org = Organization.objects.create(name="Test Org", currency_code="USD", currency_symbol="$")
        self.profile = UserProfile.objects.create(user=self.user, organization=self.org, role=UserRole.OWNER)

        self.client = Client()
        self.client.force_login(self.user)

        self.category = ProductCategory.objects.create(organization=self.org, name="Tech")
        self.product = Product.objects.create(
            organization=self.org, name="Test Router X", sku="ROUTER-TEST",
            selling_price=100.00, purchase_price=50.00, stock_quantity=10, reorder_level=5,
            product_type=ProductType.PHYSICAL, category=self.category
        )
        self.customer = Customer.objects.create(organization=self.org, company_name="Test Customer Ltd", email="cust@test.com")

    def test_dashboard_access(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Good morning")

    def test_invoice_creation_and_stock_deduction(self):
        response = self.client.post('/sales/invoices/create/', {
            'customer_id': self.customer.id,
            'date': str(timezone.now().date()),
            'due_date': str(timezone.now().date() + timedelta(days=30)),
            'product_id': [self.product.id],
            'quantity': [3],
            'unit_price': [100.00]
        })
        self.assertEqual(response.status_code, 302)

        # Verify product stock deducted by 3
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 7)

        # Verify stock movement recorded
        movement = StockMovement.objects.filter(product=self.product).first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity_change, -3)

    def test_business_ai_queries(self):
        # 1. Sales query
        ai_sales = process_ai_request("How are sales performing?", self.profile, self.org)
        self.assertIn("Your sales this month", ai_sales['text'])

        # 2. Low stock query
        self.product.stock_quantity = 2
        self.product.save()
        ai_stock = process_ai_request("Which products need reordering?", self.profile, self.org)
        self.assertIn("are below their reorder level", ai_stock['text'])

        # 3. Action drafting query
        ai_draft = process_ai_request("Create invoice for Test Customer Ltd for 10 units", self.profile, self.org)
        self.assertEqual(ai_draft['action']['type'], 'DRAFT_INVOICE')
        self.assertIn("Review Invoice", ai_draft['link']['label'])

    def test_receivables_aging(self):
        inv = Invoice.objects.create(
            organization=self.org, invoice_number="INV-TEST-01", customer=self.customer,
            date=timezone.now().date() - timedelta(days=40),
            due_date=timezone.now().date() - timedelta(days=10),
            status=InvoiceStatus.OVERDUE, total_amount=500.00, paid_amount=0.00
        )
        response = self.client.get('/finance/receivables/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "500.00")
        self.assertContains(response, "1–30 Days")
