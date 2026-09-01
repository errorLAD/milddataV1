from django.test import TestCase, Client
from django.urls import reverse
from apps.core.models import Organization, User, ActivityLog, Notification
from apps.suppliers.models import Supplier, DocumentType, OnboardingTemplate, DocumentRequirement
from apps.documents.models import SupplierDocument
from apps.compliance.models import ComplianceIssue
from apps.approvals.models import ApprovalRequest

class SupplierOSTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        self.user = User.objects.create_user(username='testadmin@supplieros.com', password='password123', organization=self.org)
        
        self.doc_type = DocumentType.objects.create(
            organization=self.org, name='Insurance Certificate', code='INS_CERT'
        )
        
        self.template = OnboardingTemplate.objects.create(
            organization=self.org, name='Test Template', supplier_category='Manufacturing'
        )
        
        self.supplier = Supplier.objects.create(
            organization=self.org,
            legal_name='Acme Testing Components',
            company_email='test@acme.com',
            status=Supplier.Status.APPROVED,
            compliance_score=100
        )
        
        self.doc = SupplierDocument.objects.create(
            organization=self.org,
            supplier=self.supplier,
            document_type=self.doc_type,
            status=SupplierDocument.Status.PENDING_REVIEW
        )

        self.compliance_issue = ComplianceIssue.objects.create(
            organization=self.org,
            supplier=self.supplier,
            document=self.doc,
            title='Test Compliance Issue',
            severity=ComplianceIssue.Severity.HIGH
        )

        self.approval_request = ApprovalRequest.objects.create(
            organization=self.org,
            supplier=self.supplier,
            status=ApprovalRequest.Status.PENDING
        )

    def test_dashboard_renders(self):
        self.client.login(username='testadmin@supplieros.com', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_suppliers_list_renders(self):
        response = self.client.get(reverse('suppliers_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acme Testing Components')

    def test_supplier_detail_renders(self):
        url = reverse('supplier_detail', kwargs={'supplier_id': self.supplier.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_supplier_renders(self):
        response = self.client.get(reverse('add_supplier'))
        self.assertEqual(response.status_code, 200)

    def test_documents_list_renders(self):
        response = self.client.get(reverse('documents_list'))
        self.assertEqual(response.status_code, 200)

    def test_document_detail_render_and_verification(self):
        url = reverse('document_detail', kwargs={'doc_id': self.doc.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Approve document
        post_response = self.client.post(url, {'action': 'approve'})
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, SupplierDocument.Status.VERIFIED)

    def test_approvals_list_renders(self):
        response = self.client.get(reverse('approvals_list'))
        self.assertEqual(response.status_code, 200)

    def test_approval_detail_renders(self):
        url = reverse('approval_detail', kwargs={'approval_id': self.approval_request.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_compliance_center_renders(self):
        response = self.client.get(reverse('compliance_center'))
        self.assertEqual(response.status_code, 200)

    def test_templates_list_renders(self):
        response = self.client.get(reverse('templates_list'))
        self.assertEqual(response.status_code, 200)

    def test_notifications_list_renders(self):
        response = self.client.get(reverse('notifications_list'))
        self.assertEqual(response.status_code, 200)

    def test_activity_log_renders(self):
        response = self.client.get(reverse('activity_log'))
        self.assertEqual(response.status_code, 200)

    def test_global_search_renders(self):
        response = self.client.get(reverse('global_search') + '?q=Acme')
        self.assertEqual(response.status_code, 200)

    def test_reports_renders(self):
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)

    def test_settings_renders(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)

    def test_supplier_portal_access(self):
        url = reverse('portal_view', kwargs={'token': self.supplier.invitation_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acme Testing Components')

