import datetime
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import Business, UserProfile
from customers.models import Customer
from udhaar.models import Udhaar
from sales.models import Sale
from payments.models import Payment
from b2bcollections.models import ReminderRule, CollectionActivity
from b2bcollections.views import get_collection_priority
from ai_advisor.services import answer_business_question
from settings_app.models import BusinessSettings


class B2BCollectionsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testowner', password='password123')
        self.business = Business.objects.create(
            name='Test B2B Enterprises',
            owner_name='Test Owner',
            phone='9876543210',
            is_active=True
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            business=self.business,
            role='Owner',
            phone='9876543210'
        )
        self.client = Client()
        self.client.login(username='testowner', password='password123')

        # Create a customer
        self.customer = Customer.objects.create(
            business=self.business,
            name='Sharma Traders',
            phone='9876543210',
            email='sharma@example.com'
        )

        # Create an overdue Udhaar / Collection
        self.today = timezone.now().date()
        self.overdue_udhaar = Udhaar.objects.create(
            business=self.business,
            customer=self.customer,
            total_amount=240000,
            paid_amount=40000,
            remaining_amount=200000,
            due_date=self.today - datetime.timedelta(days=18),
            status='Overdue'
        )

    def test_priority_scoring(self):
        priority = get_collection_priority(self.overdue_udhaar, self.today)
        self.assertIn(priority['level'], ['Urgent', 'High', 'Normal', 'Low'])
        self.assertGreater(priority['score'], 0)

    def test_landing_page_view(self):
        response = self.client.get('/landing/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'NextSlot')
        self.assertContains(response, 'Get Your B2B Invoices')

    def test_dashboard_view(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total Outstanding')
        self.assertContains(response, 'potential collection from today')

    def test_ai_collections_assistant(self):
        response = self.client.get('/ai-advisor/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Collections Assistant')

    def test_country_localization_system(self):
        from settings_app.models import BusinessSettings
        from core.localization import get_country_profile, format_money
        
        b_settings, _ = BusinessSettings.objects.get_or_create(business=self.business)

        # 1. Test United States (US) Localization Defaults
        b_settings.apply_country_defaults('US')
        b_settings.save()
        self.assertEqual(b_settings.currency, 'USD')
        self.assertEqual(b_settings.currency_symbol, '$')
        self.assertEqual(b_settings.tax_label, 'Sales Tax')
        self.assertEqual(format_money(248500, symbol=b_settings.currency_symbol), '$ 248,500')

        # 2. Test India (IN) Localization Defaults
        b_settings.apply_country_defaults('IN')
        b_settings.save()
        self.assertEqual(b_settings.currency, 'INR')
        self.assertEqual(b_settings.currency_symbol, '₹')
        self.assertEqual(b_settings.tax_label, 'GST')
        self.assertEqual(format_money(200000, symbol=b_settings.currency_symbol, number_format=b_settings.number_format), '₹ 2,00,000')

        # 3. Test United Kingdom (GB) Localization Defaults
        b_settings.apply_country_defaults('GB')
        b_settings.save()
        self.assertEqual(b_settings.currency, 'GBP')
        self.assertEqual(b_settings.currency_symbol, '£')
        self.assertEqual(b_settings.tax_label, 'VAT')
        self.assertEqual(format_money(14999, symbol=b_settings.currency_symbol), '£ 14,999')

    def test_collections_list_view(self):
        response = self.client.get('/collections/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sharma Traders')
        self.assertContains(response, 'Total Outstanding')

    def test_collections_filter_tabs(self):
        for tab in ['all', 'due_today', 'overdue', 'upcoming', 'promise', 'missed', 'paid']:
            response = self.client.get(f'/collections/?tab={tab}')
            self.assertEqual(response.status_code, 200)

    def test_set_promise_view(self):
        promise_date = (self.today + datetime.timedelta(days=5)).strftime('%Y-%m-%d')
        response = self.client.post(f'/collections/{self.overdue_udhaar.pk}/promise/', {
            'promised_date': promise_date,
            'promised_amount': '100000'
        })
        self.assertEqual(response.status_code, 302)
        self.overdue_udhaar.refresh_from_db()
        self.assertEqual(self.overdue_udhaar.status, 'Payment Promised')
        self.assertEqual(float(self.overdue_udhaar.promised_amount), 100000.0)

    def test_single_reminder_view(self):
        response = self.client.post(f'/collections/{self.overdue_udhaar.pk}/remind/', {
            'custom_message': 'Hello Sharma Traders, kindly clear your balance of ₹2,00,000.'
        })
        self.assertEqual(response.status_code, 302)
        self.overdue_udhaar.refresh_from_db()
        self.assertIsNotNone(self.overdue_udhaar.last_reminder_sent)

    def test_reports_view(self):
        response = self.client.get('/collections/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aging Schedule Breakdown')

    def test_reminder_rules_view(self):
        response = self.client.get('/collections/reminder-rules/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Reminder Schedule')

    def test_ai_collections_assistant(self):
        result = answer_business_question(self.business, 'Who should I contact today?')
        self.assertIn('Sharma Traders', result['answer'])
        self.assertEqual(result['link_url'], '/collections/?tab=due_today')

    def test_country_localization_system(self):
        settings, _ = BusinessSettings.objects.get_or_create(business=self.business)

        # 1. Test India (IN)
        settings.apply_country_defaults('IN')
        settings.save()
        self.assertEqual(settings.currency, 'INR')
        self.assertEqual(settings.currency_symbol, '₹')
        self.assertEqual(settings.tax_label, 'GST')

        # 2. Test United States (US)
        settings.apply_country_defaults('US')
        settings.save()
        self.assertEqual(settings.currency, 'USD')
        self.assertEqual(settings.currency_symbol, '$')
        self.assertEqual(settings.tax_label, 'Sales Tax')

        # 3. Test United Kingdom (GB)
        settings.apply_country_defaults('GB')
        settings.save()
        self.assertEqual(settings.currency, 'GBP')
        self.assertEqual(settings.currency_symbol, '£')
        self.assertEqual(settings.tax_label, 'VAT')
