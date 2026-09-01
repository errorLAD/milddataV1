from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
import datetime

from apps.accounts.models import Organization, UserProfile
from apps.inventory.models import Product, ProductCategory, ProductUnit, Warehouse, Inventory, StockMovement
from apps.purchasing.models import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceipt
from apps.sales.models import Customer, SalesQuote, SalesQuoteItem, SalesOrder, Invoice, InvoiceItem
from apps.finance.models import Payment
from apps.core.models import OrganizationAISetting, AIUsageLog
from apps.core.ai_copilot import StockFlowAIEngine
from apps.core.templatetags.locale_tags import money_format, date_format

class StockFlowAIAndCoreExhaustiveTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testowner', password='password123')
        self.org = Organization.objects.create(
            name='Global Nexus Test Corp',
            country='United States',
            currency_code='USD',
            currency_symbol='$',
            currency_position='prefix',
            date_format='MM/DD/YYYY',
            number_format='1,234.56',
            tax_name='Sales Tax',
            tax_rate=Decimal('8.50')
        )
        self.profile = UserProfile.objects.create(user=self.user, organization=self.org, role='OWNER')

        self.wh_main = Warehouse.objects.create(organization=self.org, name='Main WH', code='WH-MAIN', is_primary=True)
        self.wh_sec = Warehouse.objects.create(organization=self.org, name='Secondary WH', code='WH-SEC', is_primary=False)

        self.category = ProductCategory.objects.create(organization=self.org, name='Electronics')
        self.unit = ProductUnit.objects.create(organization=self.org, name='Piece', abbreviation='pcs')

        self.product = Product.objects.create(
            organization=self.org,
            name='Test Wi-Fi Router',
            sku='RT-100',
            barcode='8801928371',
            category=self.category,
            unit=self.unit,
            purchase_price=Decimal('50.00'),
            selling_price=Decimal('100.00'),
            reorder_level=5,
            opening_stock=2
        )
        Inventory.objects.create(organization=self.org, product=self.product, warehouse=self.wh_main, quantity=2)

        self.supplier = Supplier.objects.create(
            organization=self.org,
            company_name='Acme Supply Co',
            contact_person='John Smith',
            email='john@acme.com',
            country='United States',
            payment_terms='Net 30'
        )

        self.customer = Customer.objects.create(
            organization=self.org,
            company_name='Horizon Retail Inc',
            contact_person='Jane Doe',
            email='jane@horizon.com',
            country='Canada',
            payment_terms='Net 30'
        )

        self.invoice = Invoice.objects.create(
            organization=self.org,
            customer=self.customer,
            warehouse=self.wh_main,
            invoice_number='INV-1001',
            invoice_date=datetime.date.today(),
            due_date=datetime.date.today() + datetime.timedelta(days=30),
            status='UNPAID',
            subtotal=Decimal('200.00'),
            tax_amount=Decimal('17.00'),
            total_amount=Decimal('217.00'),
            paid_amount=Decimal('0.00')
        )

    # --- STOCKFLOW AI COPILOT TESTS ---
    def test_stockflow_ai_engine(self):
        engine = StockFlowAIEngine(self.org, self.user)
        result = engine.process_query("Which products are low on stock?")

        self.assertIn('RT-100', result['answer'])
        self.assertIn('Test Wi-Fi Router', result['answer'])

    def test_stockflow_ai_copilot_api(self):
        self.client.login(username='testowner', password='password123')
        res = self.client.get('/api/ai/copilot/?prompt=Who+owes+us+money?')

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertIn('Horizon Retail Inc', data['answer'])

    def test_stockflow_ai_action_proposal(self):
        self.client.login(username='testowner', password='password123')
        res = self.client.get('/api/ai/copilot/?prompt=Reorder+low+stock+items')

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['action_proposal'])
        self.assertEqual(data['action_proposal']['action_url'], '/purchasing/pos/create/')

    def test_stockflow_ai_settings_and_test_connection(self):
        self.client.login(username='testowner', password='password123')

        # Test GET AI Settings
        res = self.client.get('/settings/ai/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'StockFlow AI Configuration')

        # Test POST update settings
        post_res = self.client.post('/settings/ai/', {
            'provider': 'GEMINI',
            'api_key': 'SECURE_TEST_GEMINI_KEY_123',
            'model_name': 'gemini-1.5-flash',
            'max_daily_queries': 200,
            'is_enabled': 'on'
        })
        self.assertEqual(post_res.status_code, 302)

        setting = OrganizationAISetting.objects.get(organization=self.org)
        self.assertEqual(setting.api_key, 'SECURE_TEST_GEMINI_KEY_123')
        self.assertEqual(setting.max_daily_queries, 200)

        # Test AI Connection API
        test_res = self.client.get('/api/ai/test/')
        self.assertEqual(test_res.status_code, 200)
        self.assertTrue(test_res.json()['success'])

    # --- ALL OTHER ROUTES AUDIT ---
    def test_authenticated_routes(self):
        self.client.login(username='testowner', password='password123')
        routes = [
            '/',
            '/inventory/products/',
            f'/inventory/products/{self.product.id}/',
            '/inventory/warehouses/',
            '/inventory/movements/',
            '/purchasing/suppliers/',
            '/purchasing/pos/',
            '/sales/customers/',
            '/sales/quotes/',
            '/sales/invoices/',
            '/finance/receivables/',
            '/finance/payables/',
            '/finance/profitability/',
            '/reports/',
            '/import/',
            '/settings/ai/',
        ]
        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route failed: {r}")
