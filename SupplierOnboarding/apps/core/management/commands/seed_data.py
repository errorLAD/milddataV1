from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from apps.core.models import Organization, User, ActivityLog, Notification
from apps.suppliers.models import (
    Supplier, SupplierContact, SupplierBankDetails, SupplierTaxInformation,
    OnboardingTemplate, DocumentType, DocumentRequirement
)
from apps.documents.models import SupplierDocument
from apps.compliance.models import ComplianceIssue
from apps.approvals.models import ApprovalRequest

class Command(BaseCommand):
    help = 'Seeds SupplierOS database with realistic enterprise demo data (15 suppliers, 30+ docs, compliance issues, activity logs)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting SupplierOS Data Seeding..."))

        # 1. Create Organization
        org, _ = Organization.objects.get_or_create(
            slug='acme-global',
            defaults={'name': 'Acme Global Procurement Inc.', 'domain': 'acme-procurement.com'}
        )

        # 2. Create Users
        admin_user, _ = User.objects.get_or_create(
            username='admin@supplieros.com',
            defaults={
                'email': 'admin@supplieros.com',
                'first_name': 'Sarah',
                'last_name': 'Jenkins',
                'role': User.Role.ADMIN,
                'organization': org,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if not admin_user.password:
            admin_user.set_password('admin123')
            admin_user.save()

        manager_user, _ = User.objects.get_or_create(
            username='manager@supplieros.com',
            defaults={
                'email': 'manager@supplieros.com',
                'first_name': 'Alex',
                'last_name': 'Rivera',
                'role': User.Role.PROCUREMENT_MANAGER,
                'organization': org
            }
        )
        if not manager_user.password:
            manager_user.set_password('manager123')
            manager_user.save()

        # 3. Create Document Types
        doc_types_data = [
            ('Business Registration', 'BUS_REG', 'Company incorporation & registration certificate', 365),
            ('Tax Certificate (PAN/GST/VAT)', 'TAX_CERT', 'Tax identity & GST registration proof', 365),
            ('Bank Account Certificate', 'BANK_CERT', 'Cancelled cheque or bank account confirmation', 730),
            ('Insurance Certificate', 'INS_CERT', 'Comprehensive general liability insurance policy', 365),
            ('Address Proof', 'ADDR_PROOF', 'Utility bill or lease agreement', 365),
            ('ISO 9001 Quality Certificate', 'ISO_CERT', 'Quality management standard accreditation', 1095),
        ]

        doc_types = {}
        for name, code, desc, days in doc_types_data:
            dt, _ = DocumentType.objects.get_or_create(
                organization=org, code=code,
                defaults={'name': name, 'description': desc, 'default_expiry_days': days}
            )
            doc_types[code] = dt

        # 4. Create Templates
        template, _ = OnboardingTemplate.objects.get_or_create(
            organization=org, name='Standard Manufacturing Onboarding',
            defaults={'supplier_category': 'Manufacturing', 'description': 'Full compliance package for production vendors.'}
        )
        for dt in doc_types.values():
            DocumentRequirement.objects.get_or_create(template=template, document_type=dt, defaults={'is_mandatory': True})

        # 5. Suppliers List Data
        suppliers_raw = [
            ("ABC Components Pvt Ltd", "ABC Tech", "Manufacturing", "India", "procurement@abccomponents.com", Supplier.Status.APPROVED, 96),
            ("XYZ Logistics & Warehousing", "XYZ Express", "Logistics", "India", "info@xyzlogistics.in", Supplier.Status.IN_REVIEW, 72),
            ("Delta Industries Ltd", "Delta Mfg", "Raw Materials", "India", "contact@deltaindustries.com", Supplier.Status.APPROVED, 91),
            ("Kumar Electricals & Engineering", "Kumar Power", "Contractor", "India", "sales@kumarelectricals.com", Supplier.Status.PENDING, 40),
            ("Apex Rubber Products", "Apex Rubber", "Manufacturing", "India", "orders@apexrubber.com", Supplier.Status.APPROVED, 88),
            ("Orion Packaging Systems", "Orion Pack", "Manufacturing", "United States", "support@orionpack.com", Supplier.Status.IN_REVIEW, 65),
            ("Horizon Freight Movers", "Horizon Express", "Logistics", "United Kingdom", "dispatch@horizonfreight.co.uk", Supplier.Status.APPROVED, 94),
            ("Summit Chemical Works", "Summit Chem", "Raw Materials", "Germany", "admin@summitchem.de", Supplier.Status.SUSPENDED, 35),
            ("Vanguard Metal Tech", "Vanguard Metal", "Manufacturing", "India", "sales@vanguardmetal.in", Supplier.Status.APPROVED, 90),
            ("Atlas Cargo Services", "Atlas Cargo", "Logistics", "Singapore", "ops@atlascargo.sg", Supplier.Status.INVITED, 50),
            ("Precision Fasteners Ltd", "Precision Fasteners", "Manufacturing", "India", "info@precisionfasteners.com", Supplier.Status.APPROVED, 100),
            ("Zenith Software & IT Solutions", "Zenith Tech", "IT Hardware & Software", "India", "b2b@zenithit.com", Supplier.Status.APPROVED, 95),
            ("Sterling Paper Products", "Sterling Paper", "Raw Materials", "India", "contact@sterlingpaper.in", Supplier.Status.REJECTED, 20),
            ("Nexus Electronics India", "Nexus Electronics", "Manufacturing", "India", "supply@nexuselec.in", Supplier.Status.IN_REVIEW, 78),
            ("Phoenix Power Solutions", "Phoenix Power", "Contractor", "India", "projects@phoenixpower.com", Supplier.Status.APPROVED, 85),
        ]

        today = timezone.now().date()

        for legal_name, trading, category, country, email, status, score in suppliers_raw:
            supplier, created = Supplier.objects.get_or_create(
                organization=org, legal_name=legal_name,
                defaults={
                    'trading_name': trading,
                    'category': category,
                    'country': country,
                    'company_email': email,
                    'status': status,
                    'compliance_score': score,
                    'phone': '+91 98765 43210',
                    'city': 'Bengaluru',
                    'state': 'Karnataka',
                    'address': 'Plot 42, Industrial Zone',
                    'onboarding_deadline': today + timedelta(days=14)
                }
            )

            if created:
                # Add Contact
                SupplierContact.objects.create(
                    supplier=supplier, name=f"Contact for {legal_name}",
                    title="Head of Procurement", email=email, phone="+91 98123 45678", is_primary=True
                )
                # Add Tax Info
                SupplierTaxInformation.objects.create(
                    supplier=supplier, tax_id_number=f"PAN-{random.randint(10000,99999)}", gst_vat_number=f"27GST{random.randint(1000,9999)}1Z5"
                )
                # Add Bank Details
                SupplierBankDetails.objects.create(
                    supplier=supplier, bank_name="HDFC Bank Ltd", account_name=legal_name, account_number=f"50100{random.randint(1000000,9999999)}"
                )

                # Create Supplier Documents
                for code, dt in doc_types.items():
                    doc_status = SupplierDocument.Status.VERIFIED
                    exp_d = today + timedelta(days=random.randint(90, 365))

                    if status == Supplier.Status.INVITED or status == Supplier.Status.PENDING:
                        doc_status = SupplierDocument.Status.MISSING
                    elif legal_name == "ABC Components Pvt Ltd" and code == "INS_CERT":
                        doc_status = SupplierDocument.Status.EXPIRING_SOON
                        exp_d = today + timedelta(days=12)
                    elif legal_name == "XYZ Logistics & Warehousing" and code == "TAX_CERT":
                        doc_status = SupplierDocument.Status.MISSING
                    elif legal_name == "Summit Chemical Works" and code == "BANK_CERT":
                        doc_status = SupplierDocument.Status.REJECTED
                    elif status == Supplier.Status.IN_REVIEW:
                        doc_status = SupplierDocument.Status.PENDING_REVIEW

                    SupplierDocument.objects.create(
                        organization=org,
                        supplier=supplier,
                        document_type=dt,
                        file_name=f"{code.lower()}_{supplier.id.hex[:6]}.pdf",
                        status=doc_status,
                        issue_date=today - timedelta(days=180),
                        expiry_date=exp_d,
                        ai_extracted_data={
                            'company_name': legal_name,
                            'document_type': dt.name,
                            'verified_status': 'Valid'
                        },
                        ai_confidence=0.96,
                        ai_status=SupplierDocument.AIStatus.CONFIRMED
                    )

                # Approvals
                if status == Supplier.Status.IN_REVIEW:
                    ApprovalRequest.objects.create(
                        organization=org,
                        supplier=supplier,
                        status=ApprovalRequest.Status.PENDING,
                        risk_flags=["Supplier Portal Completed - Pending Verification"]
                    )

        # 6. Compliance Issues
        abc = Supplier.objects.filter(legal_name="ABC Components Pvt Ltd").first()
        xyz = Supplier.objects.filter(legal_name="XYZ Logistics & Warehousing").first()
        summit = Supplier.objects.filter(legal_name="Summit Chemical Works").first()

        if abc:
            ins_doc = SupplierDocument.objects.filter(supplier=abc, document_type__code="INS_CERT").first()
            ComplianceIssue.objects.get_or_create(
                organization=org, supplier=abc, document=ins_doc,
                title="Insurance certificate expires in 12 days",
                defaults={'description': 'Policy POL-839293 expires on ' + (today + timedelta(days=12)).strftime('%d %b %Y'), 'severity': ComplianceIssue.Severity.HIGH, 'due_date': today + timedelta(days=12)}
            )

        if xyz:
            ComplianceIssue.objects.get_or_create(
                organization=org, supplier=xyz,
                title="GST certificate missing from onboarding portal",
                defaults={'description': 'Vendor did not submit GST proof during portal step 2.', 'severity': ComplianceIssue.Severity.MEDIUM, 'due_date': today + timedelta(days=7)}
            )

        if summit:
            bank_doc = SupplierDocument.objects.filter(supplier=summit, document_type__code="BANK_CERT").first()
            ComplianceIssue.objects.get_or_create(
                organization=org, supplier=summit, document=bank_doc,
                title="Bank account verification cheque rejected",
                defaults={'description': 'Name mismatch on cancelled cheque.', 'severity': ComplianceIssue.Severity.CRITICAL, 'due_date': today + timedelta(days=3)}
            )

        # 7. Activity Logs
        ActivityLog.objects.create(organization=org, user=admin_user, action='System Initialized', object_type='Organization', object_name=org.name)
        ActivityLog.objects.create(organization=org, user=admin_user, action='Supplier Invited', object_type='Supplier', object_name='ABC Components Pvt Ltd')
        ActivityLog.objects.create(organization=org, user=admin_user, action='Document Verified', object_type='SupplierDocument', object_name='ISO Certificate (Delta Industries)')
        ActivityLog.objects.create(organization=org, user=manager_user, action='Compliance Issue Logged', object_type='ComplianceIssue', object_name='Insurance Expiry Alert')

        # 8. Notifications
        Notification.objects.get_or_create(
            organization=org, title="Insurance Certificate expiring soon",
            defaults={'message': 'ABC Components Insurance Certificate expires in 12 days.', 'notification_type': Notification.Type.EXPIRY, 'link': '/compliance/'}
        )
        Notification.objects.get_or_create(
            organization=org, title="New supplier submitted onboarding",
            defaults={'message': 'XYZ Logistics & Warehousing completed onboarding checklist.', 'notification_type': Notification.Type.APPROVAL, 'link': '/approvals/'}
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded 15 suppliers, 30+ documents, compliance issues, and activity logs!"))
