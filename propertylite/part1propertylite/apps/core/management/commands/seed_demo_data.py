from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
from apps.core.models import Organization, User, AuditLog, Notification
from apps.properties.models import Property, Building, Unit
from apps.tenants.models import TenantProfile
from apps.leases.models import Lease
from apps.finance.models import RentInvoice, Payment, Expense
from apps.maintenance.models import Vendor, MaintenanceTicket, TicketMaterial, TicketLabour

class Command(BaseCommand):
    help = 'Seeds database with realistic demo properties, tenants, leases, rents, maintenance, and user role accounts.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding PropFlow demo database...")

        # 1. Organization
        org, created = Organization.objects.get_or_create(
            slug='propflow-partners',
            defaults={
                'name': 'PropFlow Real Estate Partners',
                'plan': Organization.PLAN_PROFESSIONAL
            }
        )

        # 2. Users for all 6 roles
        pass_str = 'PropFlow2026!'

        def create_user(username, email, first, last, role):
            u = User.objects.filter(username=username).first()
            if not u:
                u = User.objects.create_user(
                    username=username,
                    email=email,
                    password=pass_str,
                    first_name=first,
                    last_name=last,
                    organization=org,
                    role=role
                )
            return u

        admin_user = create_user('admin@propflow.com', 'admin@propflow.com', 'Sarah', 'Jenkins', User.ROLE_SUPER_ADMIN)
        manager_user = create_user('manager@propflow.com', 'manager@propflow.com', 'Marcus', 'Vance', User.ROLE_PROPERTY_MANAGER)
        owner_user = create_user('owner@propflow.com', 'owner@propflow.com', 'Harrison', 'Sterling', User.ROLE_PROPERTY_OWNER)
        accountant_user = create_user('accountant@propflow.com', 'accountant@propflow.com', 'Elena', 'Rostova', User.ROLE_ACCOUNTANT)
        tech_user = create_user('tech@propflow.com', 'tech@propflow.com', 'David', 'Miller', User.ROLE_MAINTENANCE_STAFF)
        tenant_user = create_user('tenant@propflow.com', 'tenant@propflow.com', 'Alex', 'Morgan', User.ROLE_TENANT)

        # Additional Tenants
        t2 = create_user('jordan.lee@gmail.com', 'jordan.lee@gmail.com', 'Jordan', 'Lee', User.ROLE_TENANT)
        t3 = create_user('priya.sharma@gmail.com', 'priya.sharma@gmail.com', 'Priya', 'Sharma', User.ROLE_TENANT)

        # Tenant Profiles
        TenantProfile.objects.get_or_create(user=tenant_user, organization=org, defaults={'emergency_contact_name': 'Sarah Morgan', 'emergency_contact_phone': '+1 (512) 555-0122'})
        TenantProfile.objects.get_or_create(user=t2, organization=org, defaults={'emergency_contact_name': 'Mark Lee', 'emergency_contact_phone': '+1 (512) 555-0188'})
        TenantProfile.objects.get_or_create(user=t3, organization=org, defaults={'emergency_contact_name': 'Raj Sharma', 'emergency_contact_phone': '+1 (512) 555-0199'})

        # 3. Properties
        p1, _ = Property.objects.get_or_create(
            name='Grand Horizon Apartments',
            organization=org,
            defaults={
                'property_type': Property.TYPE_APARTMENT,
                'address': '750 Congress Avenue',
                'city': 'Austin',
                'state': 'TX',
                'zip_code': '78701',
                'owner': owner_user,
                'manager': manager_user,
                'purchase_value': 4500000.00,
                'current_value': 5200000.00
            }
        )

        p2, _ = Property.objects.get_or_create(
            name='Metropolitan Tech Center',
            organization=org,
            defaults={
                'property_type': Property.TYPE_OFFICE,
                'address': '1200 Innovation Way',
                'city': 'Austin',
                'state': 'TX',
                'zip_code': '78759',
                'owner': owner_user,
                'manager': manager_user,
                'purchase_value': 8200000.00,
                'current_value': 9400000.00
            }
        )

        p3, _ = Property.objects.get_or_create(
            name='Sunset Palms Villas',
            organization=org,
            defaults={
                'property_type': Property.TYPE_VILLA,
                'address': '420 Ocean Drive',
                'city': 'Miami',
                'state': 'FL',
                'zip_code': '33139',
                'owner': owner_user,
                'manager': manager_user,
                'purchase_value': 3100000.00,
                'current_value': 3800000.00
            }
        )

        # 4. Units for Property 1
        u101, _ = Unit.objects.get_or_create(property=p1, unit_number='101', defaults={'floor': 1, 'type': Unit.UNIT_TYPE_1BHK, 'monthly_rent': 1850.00, 'security_deposit': 1850.00, 'status': Unit.STATUS_OCCUPIED})
        u102, _ = Unit.objects.get_or_create(property=p1, unit_number='102', defaults={'floor': 1, 'type': Unit.UNIT_TYPE_2BHK, 'monthly_rent': 2400.00, 'security_deposit': 2400.00, 'status': Unit.STATUS_OCCUPIED})
        u201, _ = Unit.objects.get_or_create(property=p1, unit_number='201', defaults={'floor': 2, 'type': Unit.UNIT_TYPE_2BHK, 'monthly_rent': 2450.00, 'security_deposit': 2450.00, 'status': Unit.STATUS_OCCUPIED})
        u202, _ = Unit.objects.get_or_create(property=p1, unit_number='202', defaults={'floor': 2, 'type': Unit.UNIT_TYPE_3BHK, 'monthly_rent': 3100.00, 'security_deposit': 3100.00, 'status': Unit.STATUS_VACANT})

        # Units for Commercial Office P2
        u_ste100, _ = Unit.objects.get_or_create(property=p2, unit_number='Suite 100', defaults={'floor': 1, 'type': Unit.UNIT_TYPE_COMMERCIAL, 'monthly_rent': 6500.00, 'security_deposit': 6500.00, 'status': Unit.STATUS_OCCUPIED})
        u_ste200, _ = Unit.objects.get_or_create(property=p2, unit_number='Suite 200', defaults={'floor': 2, 'type': Unit.UNIT_TYPE_COMMERCIAL, 'monthly_rent': 8200.00, 'security_deposit': 8200.00, 'status': Unit.STATUS_VACANT})

        # 5. Leases
        today = datetime.date.today()
        start = today - datetime.timedelta(days=180)
        end = today + datetime.timedelta(days=185)
        expiring_end = today + datetime.timedelta(days=14) # Expiring soon

        l1, _ = Lease.objects.get_or_create(
            unit=u101,
            defaults={
                'organization': org,
                'property': p1,
                'tenant': tenant_user,
                'start_date': start,
                'end_date': end,
                'monthly_rent': 1850.00,
                'security_deposit': 1850.00,
                'status': Lease.STATUS_ACTIVE
            }
        )

        l2, _ = Lease.objects.get_or_create(
            unit=u102,
            defaults={
                'organization': org,
                'property': p1,
                'tenant': t2,
                'start_date': today - datetime.timedelta(days=350),
                'end_date': expiring_end,
                'monthly_rent': 2400.00,
                'security_deposit': 2400.00,
                'status': Lease.STATUS_ACTIVE
            }
        )

        l3, _ = Lease.objects.get_or_create(
            unit=u201,
            defaults={
                'organization': org,
                'property': p1,
                'tenant': t3,
                'start_date': start,
                'end_date': end,
                'monthly_rent': 2450.00,
                'security_deposit': 2450.00,
                'status': Lease.STATUS_ACTIVE
            }
        )

        # 6. Rent Invoices & Payments
        inv1, _ = RentInvoice.objects.get_or_create(
            invoice_number='INV-2026-08-101',
            defaults={
                'organization': org,
                'lease': l1,
                'unit': u101,
                'tenant': tenant_user,
                'amount': 1850.00,
                'due_date': today - datetime.timedelta(days=10),
                'status': RentInvoice.STATUS_PAID
            }
        )
        Payment.objects.get_or_create(
            invoice=inv1,
            defaults={
                'organization': org,
                'tenant': tenant_user,
                'amount': 1850.00,
                'payment_date': today - datetime.timedelta(days=12),
                'payment_method': Payment.METHOD_BANK_TRANSFER,
                'reference_number': 'ACH-88491023',
                'status': Payment.STATUS_COMPLETED
            }
        )

        inv2, _ = RentInvoice.objects.get_or_create(
            invoice_number='INV-2026-08-102',
            defaults={
                'organization': org,
                'lease': l2,
                'unit': u102,
                'tenant': t2,
                'amount': 2400.00,
                'late_fee': 50.00,
                'due_date': today - datetime.timedelta(days=15),
                'status': RentInvoice.STATUS_OVERDUE
            }
        )

        inv3, _ = RentInvoice.objects.get_or_create(
            invoice_number='INV-2026-08-201',
            defaults={
                'organization': org,
                'lease': l3,
                'unit': u201,
                'tenant': t3,
                'amount': 2450.00,
                'due_date': today + datetime.timedelta(days=5),
                'status': RentInvoice.STATUS_PENDING
            }
        )

        # 7. Vendors & Maintenance Tickets
        v1, _ = Vendor.objects.get_or_create(
            company='ProFix Plumbing & Heating',
            organization=org,
            defaults={
                'name': 'Robert Taylor',
                'category': 'Plumbing Services',
                'phone': '+1 (512) 555-8822',
                'email': 'dispatch@profix.com',
                'rating': 4.9
            }
        )

        v2, _ = Vendor.objects.get_or_create(
            company='ClimateControl HVAC Specialists',
            organization=org,
            defaults={
                'name': 'Michael Vance',
                'category': 'HVAC & Refrigeration',
                'phone': '+1 (512) 555-3311',
                'email': 'service@climatehvac.com',
                'rating': 4.7
            }
        )

        t_maint1, _ = MaintenanceTicket.objects.get_or_create(
            title='Water leakage under bathroom vanity sink',
            organization=org,
            defaults={
                'description': 'Persistent drip under master bathroom vanity causing water buildup on floor.',
                'property': p1,
                'unit': u101,
                'tenant': tenant_user,
                'category': MaintenanceTicket.CAT_PLUMBING,
                'priority': MaintenanceTicket.PRIORITY_MEDIUM,
                'status': MaintenanceTicket.STATUS_IN_PROGRESS,
                'assigned_staff': tech_user,
                'assigned_vendor': v1
            }
        )

        # Add Line Item Costs for Ticket 1
        TicketMaterial.objects.get_or_create(ticket=t_maint1, material_name='PVC P-Trap & Brass Coupling', defaults={'quantity': 1, 'unit_cost': 34.50})
        TicketMaterial.objects.get_or_create(ticket=t_maint1, material_name='Waterproofing Sealant Roll', defaults={'quantity': 2, 'unit_cost': 12.00})
        TicketLabour.objects.get_or_create(ticket=t_maint1, worker_name='John (ProFix Technician)', defaults={'hours': 2.0, 'rate': 75.00})

        t_maint2, _ = MaintenanceTicket.objects.get_or_create(
            title='AC cooling inefficient in living room',
            organization=org,
            defaults={
                'description': 'HVAC blower operating but temperature remains at 78F.',
                'property': p1,
                'unit': u102,
                'tenant': t2,
                'category': MaintenanceTicket.CAT_HVAC,
                'priority': MaintenanceTicket.PRIORITY_HIGH,
                'status': MaintenanceTicket.STATUS_NEW
            }
        )

        # 8. Operating Expenses
        Expense.objects.get_or_create(
            description='Q3 Municipal Water & Sewer Utility Bill',
            organization=org,
            property=p1,
            defaults={
                'category': Expense.CAT_UTILITIES,
                'amount': 840.00,
                'date': today - datetime.timedelta(days=5),
                'vendor_name': 'Austin Water Utility'
            }
        )

        Expense.objects.get_or_create(
            description='Bi-weekly Building Common Area Cleaning',
            organization=org,
            property=p1,
            defaults={
                'category': Expense.CAT_CLEANING,
                'amount': 450.00,
                'date': today - datetime.timedelta(days=12),
                'vendor_name': 'Sparkle Janitorial Services'
            }
        )

        # 9. Audit Logs & Notifications
        AuditLog.objects.get_or_create(
            action='System Seed Completed',
            organization=org,
            defaults={
                'user': admin_user,
                'entity_type': 'System',
                'details': 'Populated realistic demo data for PropFlow SaaS.'
            }
        )

        Notification.objects.get_or_create(
            title='Rent Due Notice',
            recipient=tenant_user,
            organization=org,
            defaults={
                'message': 'Your monthly rent for Unit 101 has been processed.',
                'notification_type': Notification.TYPE_RENT_DUE
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded PropFlow SaaS demo data!"))
