import time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Business, UserProfile
from core.models import SecurityAuditLog
from core.rate_limiter import is_rate_limited, record_attempt


class GuestModeAndSecurityTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_guest_login_initialization(self):
        """Verify guest login creates demo session, demo business, and audit log."""
        response = self.client.get(reverse('accounts:guest_login'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard:index'))
        
        session = self.client.session
        self.assertTrue(session.get('is_guest'))
        self.assertIsNotNone(session.get('guest_session_id'))

        # Verify Demo Business creation
        demo_b = Business.objects.filter(name="Demo Guest Business").first()
        self.assertIsNotNone(demo_b)

        # Verify Security Audit Log
        audit_log = SecurityAuditLog.objects.filter(event_type='GUEST_LOGIN').first()
        self.assertIsNotNone(audit_log)

    def test_guest_server_side_restriction_on_post(self):
        """Verify guests are restricted from POST actions on protected endpoints."""
        self.client.get(reverse('accounts:guest_login'))
        
        # Attempt to create customer as guest via POST
        response = self.client.post(reverse('customers:create'), {
            'name': 'Hacker Customer',
            'phone': '1234567890'
        })
        # Guest middleware should block and redirect to upgrade page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/upgrade-guest/', response.url)

        # Verify access denied audit log
        audit_log = SecurityAuditLog.objects.filter(event_type='ACCESS_DENIED').first()
        self.assertIsNotNone(audit_log)

    def test_guest_upgrade_to_full_account(self):
        """Verify guest can upgrade to a full account cleanly."""
        self.client.get(reverse('accounts:guest_login'))
        self.assertTrue(self.client.session.get('is_guest'))

        response = self.client.post(reverse('accounts:upgrade_guest'), {
            'business_name': 'My Real Business',
            'owner_name': 'John Doe',
            'country': 'US',
            'phone': '9876543210',
            'email': 'john@realbusiness.com',
            'username': 'johndoe',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!'
        })
        self.assertEqual(response.status_code, 302)

        # Verify user and business registered
        user = User.objects.filter(username='johndoe').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.profile.business.name, 'My Real Business')

        # Verify guest session cleared
        self.assertFalse(self.client.session.get('is_guest', False))

        # Verify Audit Log
        audit_log = SecurityAuditLog.objects.filter(event_type='GUEST_UPGRADE').first()
        self.assertIsNotNone(audit_log)

    def test_rate_limiter_logic(self):
        """Verify rate limiter blocks IPs after max attempts."""
        test_ip = "192.168.1.100"
        for _ in range(5):
            record_attempt(test_ip, 'login')
        self.assertTrue(is_rate_limited(test_ip, 'login'))
