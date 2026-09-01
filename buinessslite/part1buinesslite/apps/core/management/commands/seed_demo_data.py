from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime
import random

from apps.core.models import Organization, UserProfile, UserRole, AuditLog, Notification, NotificationType
from apps.people.models import Employee, Attendance, AttendanceStatus, LeaveRequest, LeaveType, LeaveStatus, EmployeeDocument, DocType, SalaryPayment
from apps.inventory.models import Product, ProductCategory, Warehouse, StockMovement, MovementType, ProductType
from apps.purchasing.models import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem, POStatus
from apps.sales.models import Customer, Quote, QuoteItem, SalesOrder, SalesOrderItem, Invoice, InvoiceItem, InvoiceStatus, Payment, PaymentMethod, QuoteStatus, OrderStatus
from apps.finance.models import Expense, ExpenseCategory
from apps.operations.models import Task, TaskPriority, TaskStatus, CalendarEvent, BusinessDocument, DocCategory

class Command(BaseCommand):
    help = 'Seeds realistic international demo data for BusinessLite'

    def handle(self, *args, **options):
        self.stdout.write("Seeding BusinessLite demo data...")

        # 1. User & Demo Organization
        user, _ = User.objects.get_or_create(username='admin@businesslite.com', defaults={'email': 'admin@businesslite.com'})
        user.set_password('demo123')
        user.save()

        org, _ = Organization.objects.get_or_create(
            name="MildData BusinessLite",
            defaults={
                'country': "India",
                'currency_code': "INR",
                'currency_symbol': "₹",
                'timezone': "UTC",
                'tax_name': "GST",
                'tax_rate': 18.00,
                'invoice_prefix': "INV-",
                'po_prefix': "PO-"
            }
        )

        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'organization': org, 'role': UserRole.OWNER})

        # 2. Warehouses (2 locations)
        wh1, _ = Warehouse.objects.get_or_create(organization=org, name="Main Central Warehouse", location_code="WH-01", is_default=True)
        wh2, _ = Warehouse.objects.get_or_create(organization=org, name="East Coast Distribution Center", location_code="WH-02")

        # 3. Product Categories & Products (20 products)
        cat_tech, _ = ProductCategory.objects.get_or_create(organization=org, name="Hardware & Networking")
        cat_office, _ = ProductCategory.objects.get_or_create(organization=org, name="Office Supplies")
        cat_cables, _ = ProductCategory.objects.get_or_create(organization=org, name="Electrical Cables")
        cat_service, _ = ProductCategory.objects.get_or_create(organization=org, name="Professional Services")

        sample_products = [
            ("ABC High-Speed Ethernet Cable 50m", "CABLE-50M", "8901001", cat_cables, 15.00, 29.99, 10, 120, ProductType.PHYSICAL),
            ("Gigabit Wireless Router X", "ROUTER-X", "8901002", cat_tech, 45.00, 89.99, 15, 8, ProductType.PHYSICAL), # Low stock
            ("Heavy Duty Electric Motor 24V", "MOTOR-24V", "8901003", cat_tech, 120.00, 240.00, 5, 2, ProductType.PHYSICAL), # Low stock
            ("Industrial Fiber Optic Patch Cord", "FIBER-PC", "8901004", cat_cables, 12.50, 25.00, 20, 85, ProductType.PHYSICAL),
            ("Unmanaged 24-Port PoE Switch", "SWITCH-24P", "8901005", cat_tech, 85.00, 175.00, 8, 4, ProductType.PHYSICAL), # Low stock
            ("Dual Band Wi-Fi Access Point", "WIFI-AP", "8901006", cat_tech, 35.00, 79.99, 10, 45, ProductType.PHYSICAL),
            ("Cat6 RJ45 Connectors Box of 100", "RJ45-100", "8901007", cat_cables, 8.00, 19.99, 15, 3, ProductType.PHYSICAL), # Low stock
            ("Server Rack Cabinet 42U", "RACK-42U", "8901008", cat_tech, 350.00, 750.00, 2, 6, ProductType.PHYSICAL),
            ("Smart UPS Battery Backup 1500VA", "UPS-1500", "8901009", cat_tech, 110.00, 220.00, 5, 18, ProductType.PHYSICAL),
            ("HDMI 2.1 Ultra HD Cable 5m", "HDMI-5M", "8901010", cat_cables, 6.00, 14.99, 25, 140, ProductType.PHYSICAL),
            ("Ergonomic Mesh Office Chair", "CHAIR-MESH", "8901011", cat_office, 75.00, 160.00, 10, 22, ProductType.PHYSICAL),
            ("Standing Desk Converter Dual Monitor", "DESK-CONV", "8901012", cat_office, 95.00, 199.99, 5, 12, ProductType.PHYSICAL),
            ("Thermal Receipt Printer USB/Ethernet", "PRINT-POS", "8901013", cat_tech, 65.00, 135.00, 8, 1, ProductType.PHYSICAL), # Low stock
            ("Handheld Bluetooth Barcode Scanner", "SCAN-BT", "8901014", cat_tech, 40.00, 89.00, 10, 3, ProductType.PHYSICAL), # Low stock
            ("Label Printer Roll 500 Sheets", "ROLL-500", "8901015", cat_office, 4.50, 11.99, 30, 210, ProductType.PHYSICAL),
            ("USB-C Multi-Port Docking Station", "DOCK-USBC", "8901016", cat_tech, 42.00, 95.00, 10, 38, ProductType.PHYSICAL),
            ("Surge Protector Power Strip 8-Outlet", "POWER-8", "8901017", cat_cables, 9.00, 21.99, 20, 95, ProductType.PHYSICAL),
            ("Network Setup & Installation Service", "SERV-NET", "", cat_service, 0.00, 150.00, 0, 0, ProductType.SERVICE),
            ("On-Site Hardware Repair (Hourly)", "SERV-REPAIR", "", cat_service, 0.00, 95.00, 0, 0, ProductType.SERVICE),
            ("Annual IT Support Maintenance Plan", "SERV-MAINT", "", cat_service, 0.00, 1200.00, 0, 0, ProductType.SERVICE),
        ]

        product_objects = []
        for name, sku, barcode, cat, cost, price, reorder, stock, ptype in sample_products:
            p, _ = Product.objects.get_or_create(
                organization=org, sku=sku,
                defaults={
                    'name': name, 'barcode': barcode, 'category': cat,
                    'purchase_price': cost, 'selling_price': price,
                    'reorder_level': reorder, 'stock_quantity': stock,
                    'product_type': ptype, 'warehouse': wh1
                }
            )
            product_objects.append(p)

        # 4. Customers (10 customers)
        sample_customers = [
            ("ABC Construction Ltd", "John Miller", "john@abcconstruction.com", "+1 555 0101", "United States"),
            ("Metro Logistics & Trade", "Sarah Jenkins", "sarah@metrologistics.com", "+1 555 0102", "United States"),
            ("Global Apex Solutions", "David Chen", "david@globalapex.com", "+44 20 7946 0123", "United Kingdom"),
            ("Vanguard Auto Repair", "Michael Vance", "mike@vanguardauto.com", "+1 555 0104", "United States"),
            ("Horizon Tech Digital", "Elena Rostova", "elena@horizontech.io", "+49 30 123456", "Germany"),
            ("Pacific Retail Outlets", "Robert Taylor", "robert@pacificretail.com", "+1 555 0106", "United States"),
            ("Summit Engineering Works", "Karen Adams", "karen@summiteng.com", "+1 555 0107", "United States"),
            ("Beacon Media Agency", "Tom Wilson", "tom@beaconmedia.com", "+1 555 0108", "United States"),
            ("Starlight Cafe & Trading", "Lisa Ray", "lisa@starlighttrade.com", "+61 2 9876 5432", "Australia"),
            ("Nordic Import Export", "Lars Olsen", "lars@nordicimport.no", "+47 22 123456", "Norway"),
        ]

        customer_objects = []
        for name, contact, email, phone, country in sample_customers:
            c, _ = Customer.objects.get_or_create(
                organization=org, company_name=name,
                defaults={'contact_person': contact, 'email': email, 'phone': phone, 'country': country}
            )
            customer_objects.append(c)

        # 5. Suppliers (8 suppliers)
        sample_suppliers = [
            ("ABC Supplies Co", "Mark Davis", "orders@abcsupplies.com", "+1 555 0201", "United States"),
            ("Global Electronics Wholesale", "Anna Smith", "sales@globalelec.com", "+1 555 0202", "United States"),
            ("Apex Manufacturing Inc", "James Brown", "info@apexmfg.com", "+1 555 0203", "United States"),
            ("Euro Cable Components", "Peter Weber", "sales@eurocable.de", "+49 40 987654", "Germany"),
            ("Pacific Tech Distributors", "Kenji Sato", "orders@pacifictech.jp", "+81 3 1234 5678", "Japan"),
            ("Vanguard Office Systems", "Laura Croft", "laura@vanguardoffice.com", "+1 555 0206", "United States"),
            ("Matrix Component Works", "Steve Rogers", "steve@matrixworks.com", "+1 555 0207", "United States"),
            ("Omni Tools & Hardware", "Bruce Wayne", "bruce@omnitools.com", "+1 555 0208", "United States"),
        ]

        supplier_objects = []
        for name, contact, email, phone, country in sample_suppliers:
            s, _ = Supplier.objects.get_or_create(
                organization=org, company_name=name,
                defaults={'contact_person': contact, 'email': email, 'phone': phone, 'country': country}
            )
            supplier_objects.append(s)

        # 6. Employees (10 employees)
        sample_employees = [
            ("Alex Morgan", "Sales Manager", "Sales", "alex@businesslite.com", "+1 555 0301", 4500.00),
            ("Brian Cole", "Warehouse Supervisor", "Inventory", "brian@businesslite.com", "+1 555 0302", 3800.00),
            ("Catherine Kelly", "Senior Accountant", "Finance", "catherine@businesslite.com", "+1 555 0303", 4200.00),
            ("Daniel Vance", "Operations Coordinator", "Operations", "daniel@businesslite.com", "+1 555 0304", 3600.00),
            ("Emma Watson", "Customer Support Specialist", "Support", "emma@businesslite.com", "+1 555 0305", 3200.00),
            ("Frank Wright", "Inventory Clerk", "Inventory", "frank@businesslite.com", "+1 555 0306", 3000.00),
            ("Grace Hopper", "IT Administrator", "IT", "grace@businesslite.com", "+1 555 0307", 4800.00),
            ("Henry Ford", "Procurement Agent", "Purchasing", "henry@businesslite.com", "+1 555 0308", 3900.00),
            ("Isabella Ross", "Sales Associate", "Sales", "isabella@businesslite.com", "+1 555 0309", 3100.00),
            ("Jack Sparrow", "Logistics Driver", "Logistics", "jack@businesslite.com", "+1 555 0310", 2900.00),
        ]

        emp_objects = []
        today = timezone.now().date()
        for name, title, dept, email, phone, sal in sample_employees:
            e, _ = Employee.objects.get_or_create(
                organization=org, name=name,
                defaults={'job_title': title, 'department': dept, 'email': email, 'phone': phone, 'start_date': today - timedelta(days=180), 'basic_salary': sal}
            )
            emp_objects.append(e)

        # Attendance records for today (with 2 absent)
        for idx, emp in enumerate(emp_objects):
            status = AttendanceStatus.ABSENT if idx in [1, 5] else AttendanceStatus.PRESENT
            Attendance.objects.update_or_create(organization=org, employee=emp, date=today, defaults={'status': status})

        # Salary Payments seeding
        modes = ['Bank Transfer', 'UPI / Online', 'Cash', 'Check']
        for idx, emp in enumerate(emp_objects):
            m = modes[idx % len(modes)]
            SalaryPayment.objects.get_or_create(
                organization=org, employee=emp, payment_date=today - timedelta(days=10),
                defaults={'amount': emp.basic_salary, 'payment_mode': m, 'reference_number': f"PAYROLL-AUG-{idx+1:02d}", 'notes': "Monthly salary payout"}
            )

        # 7. Invoices (20 invoices with mixed statuses, including 3 overdue)
        invoice_objects = []
        for i in range(1, 21):
            cust = customer_objects[(i - 1) % len(customer_objects)]
            date_val = today - timedelta(days=(21 - i) * 3)
            
            # Make 3 invoices overdue
            if i in [2, 5, 8]:
                due_val = date_val - timedelta(days=10) # overdue
                status = InvoiceStatus.OVERDUE
            elif i % 2 == 0:
                due_val = date_val + timedelta(days=30)
                status = InvoiceStatus.PAID
            else:
                due_val = date_val + timedelta(days=30)
                status = InvoiceStatus.UNPAID

            inv_num = f"INV-10{i:02d}"
            inv, _ = Invoice.objects.get_or_create(
                organization=org, invoice_number=inv_num,
                defaults={'customer': cust, 'date': date_val, 'due_date': due_val, 'status': status}
            )
            
            # Line items
            p1 = product_objects[i % len(product_objects)]
            p2 = product_objects[(i + 3) % len(product_objects)]
            
            qty1, qty2 = 2, 5
            total = (qty1 * float(p1.selling_price)) + (qty2 * float(p2.selling_price))
            inv.total_amount = total
            if status == InvoiceStatus.PAID:
                inv.paid_amount = total
            elif status == InvoiceStatus.UNPAID or status == InvoiceStatus.OVERDUE:
                inv.paid_amount = 0.0
            inv.save()

            InvoiceItem.objects.get_or_create(invoice=inv, product=p1, defaults={'description': p1.name, 'quantity': qty1, 'unit_price': p1.selling_price, 'line_total': qty1 * float(p1.selling_price)})
            InvoiceItem.objects.get_or_create(invoice=inv, product=p2, defaults={'description': p2.name, 'quantity': qty2, 'unit_price': p2.selling_price, 'line_total': qty2 * float(p2.selling_price)})

            # Payments for paid invoices
            if status == InvoiceStatus.PAID:
                Payment.objects.get_or_create(
                    organization=org, invoice=inv, customer=cust, payment_number=f"PAY-{inv.id}",
                    defaults={'date': date_val + timedelta(days=2), 'amount': total, 'payment_method': PaymentMethod.BANK_TRANSFER}
                )

        # 8. Purchase Orders (10 purchases, 1 pending)
        for i in range(1, 11):
            supp = supplier_objects[i % len(supplier_objects)]
            po_num = f"PO-20{i:02d}"
            po_status = POStatus.DRAFT if i == 1 else POStatus.COMPLETED

            po, _ = PurchaseOrder.objects.get_or_create(
                organization=org, po_number=po_num,
                defaults={'supplier': supp, 'date': today - timedelta(days=i * 4), 'status': po_status, 'total_amount': 500.00 * i}
            )

        # 9. Expenses
        cat_rent, _ = ExpenseCategory.objects.get_or_create(organization=org, name="Rent & Premises")
        cat_util, _ = ExpenseCategory.objects.get_or_create(organization=org, name="Utilities & Internet")
        cat_soft, _ = ExpenseCategory.objects.get_or_create(organization=org, name="Software & Subscriptions")
        cat_trans, _ = ExpenseCategory.objects.get_or_create(organization=org, name="Transport & Fuel")

        sample_expenses = [
            ("Office Premises Rent August", 2000.00, cat_rent, "Metro Property Management"),
            ("High Speed Fiber Internet Bill", 640.00, cat_util, "Telecom Corp"),
            ("Cloud Hosting & SaaS Subscriptions", 450.00, cat_soft, "Amazon Web Services"),
            ("Delivery Truck Fuel & Transport", 510.00, cat_trans, "Shell Energy"),
            ("Office Supplies & Stationery", 280.00, cat_rent, "Staples Direct"),
        ]

        for title, amt, cat, vendor in sample_expenses:
            Expense.objects.get_or_create(
                organization=org, title=title,
                defaults={'amount': amt, 'category': cat, 'vendor': vendor, 'date': today - timedelta(days=5)}
            )

        # 10. Tasks & Documents
        Task.objects.get_or_create(organization=org, title="Review Q3 Overdue Receivables", defaults={'due_date': today + timedelta(days=2), 'priority': TaskPriority.HIGH, 'status': TaskStatus.TO_DO})
        Task.objects.get_or_create(organization=org, title="Reorder Router X & Motor 24V", defaults={'due_date': today + timedelta(days=1), 'priority': TaskPriority.MEDIUM, 'status': TaskStatus.IN_PROGRESS})

        BusinessDocument.objects.get_or_create(organization=org, title="Commercial Lease Contract", defaults={'category': DocCategory.CONTRACTS, 'expiry_date': today + timedelta(days=15)})
        BusinessDocument.objects.get_or_create(organization=org, title="City Business Operating License", defaults={'category': DocCategory.LICENSES, 'expiry_date': today + timedelta(days=20)})

        # 11. Initial Notifications & Audit Log
        Notification.objects.get_or_create(
            organization=org, title="3 Invoices Overdue",
            defaults={'message': "3 customer invoices have passed their payment due date.", 'notification_type': NotificationType.OVERDUE_INVOICE, 'link': "/finance/receivables/"}
        )
        Notification.objects.get_or_create(
            organization=org, title="Low Stock Warning",
            defaults={'message': "7 products have fallen below their reorder threshold.", 'notification_type': NotificationType.LOW_STOCK, 'link': "/inventory/products/?filter=low_stock"}
        )

        AuditLog.objects.create(
            organization=org, user=user, action="Demo Data Seeded",
            model_name="System", details="Seeded 20 products, 10 customers, 8 suppliers, 10 employees, 20 invoices, 10 POs, expenses, tasks, and audit logs."
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded BusinessLite demo data! Login with admin@businesslite.com / demo123"))
