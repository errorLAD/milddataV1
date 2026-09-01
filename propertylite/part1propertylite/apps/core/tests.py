from django.test import TestCase, Client
from django.urls import reverse
from apps.core.models import Organization, User, GuestSession
from apps.properties.models import Property, Unit
from apps.leases.models import Lease
from apps.finance.models import RentInvoice, Payment
from apps.maintenance.models import MaintenanceTicket, TicketMaterial, TicketLabour
from decimal import Decimal

class PropFlowSaaSTestCase(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        self.manager = User.objects.create_user(
            username='mgr@test.com', email='mgr@test.com', password='password',
            organization=self.org, role=User.ROLE_PROPERTY_MANAGER
        )
        self.tenant = User.objects.create_user(
            username='tenant@test.com', email='tenant@test.com', password='password',
            organization=self.org, role=User.ROLE_TENANT
        )
        self.property = Property.objects.create(
            name='Test Manor', organization=self.org, property_type=Property.TYPE_APARTMENT,
            address='123 Test St', city='Austin', state='TX', zip_code='78701'
        )
        self.unit = Unit.objects.create(
            property=self.property, unit_number='101', monthly_rent=2000.00, security_deposit=2000.00
        )
        self.lease = Lease.objects.create(
            organization=self.org, property=self.property, unit=self.unit, tenant=self.tenant,
            start_date='2026-01-01', end_date='2026-12-31', monthly_rent=2000.00, security_deposit=2000.00
        )

    def test_property_occupancy_rate(self):
        self.assertEqual(self.property.occupancy_rate, 0.0)
        self.unit.status = Unit.STATUS_OCCUPIED
        self.unit.save()
        self.assertEqual(self.property.occupancy_rate, 100.0)

    def test_maintenance_cost_calculation(self):
        ticket = MaintenanceTicket.objects.create(
            organization=self.org, title='Fix Sink', description='Leak under sink',
            property=self.property, unit=self.unit, tenant=self.tenant
        )
        TicketMaterial.objects.create(ticket=ticket, material_name='Pipe', quantity=2, unit_cost=15.00)
        TicketLabour.objects.create(ticket=ticket, worker_name='Joe', hours=2, rate=50.00)
        
        self.assertEqual(ticket.materials_cost, Decimal('30.00'))
        self.assertEqual(ticket.labour_cost, Decimal('100.00'))
        self.assertEqual(ticket.actual_total_cost, Decimal('130.00'))

    def test_invoice_balance_and_payment(self):
        inv = RentInvoice.objects.create(
            organization=self.org, lease=self.lease, unit=self.unit, tenant=self.tenant,
            invoice_number='INV-TEST-001', amount=2000.00, due_date='2026-08-01'
        )
        self.assertEqual(inv.balance_due, Decimal('2000.00'))

        Payment.objects.create(
            organization=self.org, invoice=inv, tenant=self.tenant, amount=1200.00,
            payment_date='2026-08-02', status=Payment.STATUS_COMPLETED
        )
        self.assertEqual(inv.total_paid, Decimal('1200.00'))
        self.assertEqual(inv.balance_due, Decimal('800.00'))

    def test_global_search_api(self):
        client = Client()
        client.login(username='mgr@test.com', password='password')
        response = client.get(reverse('global_search') + '?q=Manor')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data['results']) > 0)

    def test_guest_login_and_restrictions(self):
        client = Client()
        # 1. Guest login view
        response = client.get(reverse('guest_login'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_guest)

        # 2. Server-side Guest restriction check: Guest cannot create properties
        create_resp = client.get(reverse('property_create'), follow=True)
        self.assertRedirects(create_resp, reverse('guest_upgrade'))

    def test_security_headers(self):
        client = Client()
        response = client.get(reverse('landing_page'))
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.headers['Referrer-Policy'], 'same-origin')
