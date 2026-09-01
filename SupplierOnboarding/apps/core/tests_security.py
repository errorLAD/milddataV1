import io
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from apps.core.models import Organization, User
from apps.core.security import validate_file_upload, ALLOWED_EXTENSIONS
from apps.suppliers.models import Supplier

class SecurityAndGuestModeTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(name='Security Test Org', slug='sec-org')
        self.supplier = Supplier.objects.create(
            organization=self.org,
            legal_name='Security Demo Vendor',
            company_email='vendor@sec.com',
            status=Supplier.Status.APPROVED
        )

    def test_guest_login_mode(self):
        res = self.client.get(reverse('guest_login'))
        self.assertEqual(res.status_code, 302)
        
        # Check session
        session = self.client.session
        self.assertTrue(session.get('is_guest'))
        
        # Access dashboard as Guest
        dash_res = self.client.get(reverse('dashboard'))
        self.assertEqual(dash_res.status_code, 200)
        self.assertContains(dash_res, 'Guest Mode Active')

    def test_guest_forbidden_decorator_blocks_posts(self):
        # Initialize Guest Session
        self.client.get(reverse('guest_login'))
        
        # Try creating a supplier as Guest
        post_res = self.client.post(reverse('add_supplier'), {
            'legal_name': 'Hacker Supplier Inc.',
            'company_email': 'hacker@test.com'
        })
        self.assertEqual(post_res.status_code, 302) # Redirected back with error
        self.assertFalse(Supplier.objects.filter(legal_name='Hacker Supplier Inc.').exists())

    def test_security_headers_present(self):
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(res.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertIn('Content-Security-Policy', res.headers)

    def test_file_upload_validator_rejects_dangerous_extensions(self):
        bad_file = SimpleUploadedFile("malicious_script.sh", b"echo 'hack'", content_type="text/x-sh")
        with self.assertRaises(ValidationError):
            validate_file_upload(bad_file)

    def test_file_upload_validator_accepts_valid_pdf(self):
        good_file = SimpleUploadedFile("license_cert.pdf", b"%PDF-1.4 dummy pdf content", content_type="application/pdf")
        safe_name = validate_file_upload(good_file)
        self.assertTrue(safe_name.endswith('.pdf'))

    def test_user_registration_flow(self):
        res = self.client.post(reverse('register'), {
            'org_name': 'New Enterprise Ltd',
            'email': 'newadmin@enterprise.com',
            'password': 'SecurePassword123!',
            'first_name': 'Security',
            'last_name': 'Admin'
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(User.objects.filter(username='newadmin@enterprise.com').exists())
