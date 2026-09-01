from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
import datetime
import random

from apps.accounts.models import Organization, UserProfile
from apps.inventory.models import Product, ProductCategory, ProductUnit, Warehouse, Inventory, StockMovement
from apps.purchasing.models import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem, PurchaseBill
from apps.sales.models import Customer, SalesQuote, SalesQuoteItem, SalesOrder, SalesOrderItem, Invoice, InvoiceItem
from apps.finance.models import Payment
from apps.core.models import Notification, AuditLog

class Command(BaseCommand):
    help = 'Seeds realistic international SMB demo data for StockFlow'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting StockFlow demo data seeding..."))

        # 1. User & Organization
        user, created = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@stockflow.app',
            'first_name': 'Alex',
            'last_name': 'Morgan',
            'is_staff': True,
            'is_superuser': True
        })
        if created:
            user.set_password('admin123')
            user.save()

        org, _ = Organization.objects.get_or_create(name='Global Nexus Supplies', defaults={
            'country': 'United States',
            'currency_code': 'USD',
            'currency_symbol': '$',
            'currency_position': 'prefix',
            'decimal_places': 2,
            'date_format': 'MM/DD/YYYY',
            'number_format': '1,234.56',
            'timezone': 'America/New_York',
            'tax_name': 'Sales Tax',
            'tax_rate': Decimal('8.50'),
            'tax_id_label': 'EIN / Tax ID',
            'tax_id_value': 'US-987654321',
            'address': '750 3rd Avenue, Suite 1400, New York, NY 10017',
            'phone': '+1 (212) 555-0199',
            'email': 'operations@globalnexus.com',
            'website': 'https://globalnexus.example.com'
        })

        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={
            'organization': org,
            'role': 'OWNER',
            'phone': '+1 (212) 555-0190'
        })
        if profile.organization != org:
            profile.organization = org
            profile.save()

        # 2. Warehouses
        wh_main, _ = Warehouse.objects.get_or_create(organization=org, code='WH-MAIN', defaults={
            'name': 'Main Distribution Center',
            'address': '100 Logistics Way, Newark, NJ 07102',
            'is_primary': True
        })

        wh_london, _ = Warehouse.objects.get_or_create(organization=org, code='WH-LON', defaults={
            'name': 'London Hub',
            'address': 'Unit 4 Docklands Trade Park, London E16 2AB, UK',
            'is_primary': False
        })

        wh_store, _ = Warehouse.objects.get_or_create(organization=org, code='WH-NY1', defaults={
            'name': 'New York Retail Store',
            'address': '124 W 34th St, New York, NY 10001',
            'is_primary': False
        })

        warehouses = [wh_main, wh_london, wh_store]

        # 3. Product Categories & Units
        cat_net, _ = ProductCategory.objects.get_or_create(organization=org, name='Networking Equipment')
        cat_ind, _ = ProductCategory.objects.get_or_create(organization=org, name='Industrial Automation')
        cat_off, _ = ProductCategory.objects.get_or_create(organization=org, name='Smart Office Electronics')
        cat_cmp, _ = ProductCategory.objects.get_or_create(organization=org, name='Components & Sensors')
        cat_srv, _ = ProductCategory.objects.get_or_create(organization=org, name='Professional Services')

        unit_pcs, _ = ProductUnit.objects.get_or_create(organization=org, name='Piece', abbreviation='pcs')
        unit_box, _ = ProductUnit.objects.get_or_create(organization=org, name='Box (10x)', abbreviation='box')
        unit_set, _ = ProductUnit.objects.get_or_create(organization=org, name='Kit/Set', abbreviation='set')
        unit_hrs, _ = ProductUnit.objects.get_or_create(organization=org, name='Hour', abbreviation='hr')

        # 4. 25 Products
        sample_products = [
            ("Enterprise Wi-Fi 6 Router", "WR-6000", "880192837101", cat_net, unit_pcs, Decimal('120.00'), Decimal('210.00'), 15, 'PHYSICAL'),
            ("24-Port Gigabit Managed Switch", "SW-24G", "880192837102", cat_net, unit_pcs, Decimal('180.00'), Decimal('320.00'), 10, 'PHYSICAL'),
            ("Fiber Optic Transceiver 10G", "TR-10G", "880192837103", cat_net, unit_pcs, Decimal('35.00'), Decimal('75.00'), 25, 'PHYSICAL'),
            ("Cat6 Ethernet Cable (300m Box)", "CB-CAT6", "880192837104", cat_net, unit_box, Decimal('65.00'), Decimal('115.00'), 12, 'PHYSICAL'),
            ("Patch Panel 48-Port Cat6", "PP-48C6", "880192837105", cat_net, unit_pcs, Decimal('45.00'), Decimal('85.00'), 8, 'PHYSICAL'),

            ("Programmable Logic Controller (PLC)", "PLC-X10", "880192837201", cat_ind, unit_pcs, Decimal('450.00'), Decimal('790.00'), 5, 'PHYSICAL'),
            ("Industrial Optical Sensor 24V", "SN-OPT24", "880192837202", cat_ind, unit_pcs, Decimal('28.00'), Decimal('58.00'), 20, 'PHYSICAL'),
            ("Variable Frequency Drive 5.5kW", "VFD-55", "880192837203", cat_ind, unit_pcs, Decimal('310.00'), Decimal('540.00'), 6, 'PHYSICAL'),
            ("DIN-Rail Power Supply 24V 10A", "PS-DIN24", "880192837204", cat_ind, unit_pcs, Decimal('40.00'), Decimal('78.00'), 15, 'PHYSICAL'),
            ("Digital Pressure Transmitter", "PT-100", "880192837205", cat_ind, unit_pcs, Decimal('95.00'), Decimal('175.00'), 8, 'PHYSICAL'),

            ("Smart Conference Hub Camera", "CAM-CONF4K", "880192837301", cat_off, unit_pcs, Decimal('290.00'), Decimal('499.00'), 6, 'PHYSICAL'),
            ("Dual-Monitor Arm Desk Mount", "ARM-DUAL", "880192837302", cat_off, unit_pcs, Decimal('38.00'), Decimal('79.00'), 14, 'PHYSICAL'),
            ("Ergonomic Mesh Task Chair", "CHR-ERGO1", "880192837303", cat_off, unit_pcs, Decimal('140.00'), Decimal('260.00'), 8, 'PHYSICAL'),
            ("USB-C Thunderbolt 4 Docking Station", "DK-TB4", "880192837304", cat_off, unit_pcs, Decimal('110.00'), Decimal('195.00'), 10, 'PHYSICAL'),
            ("Smart LED Desk Light with Wireless Charge", "LT-SMART", "880192837305", cat_off, unit_pcs, Decimal('25.00'), Decimal('55.00'), 12, 'PHYSICAL'),

            ("Microcontroller Board v4", "MCU-V4", "880192837401", cat_cmp, unit_pcs, Decimal('12.00'), Decimal('24.00'), 50, 'PHYSICAL'),
            ("Temperature & Humidity Sensor Mod", "SN-TH02", "880192837402", cat_cmp, unit_pcs, Decimal('4.50'), Decimal('9.90'), 40, 'PHYSICAL'),
            ("Relay Module 4-Channel 5V", "RL-4CH", "880192837403", cat_cmp, unit_pcs, Decimal('3.20'), Decimal('7.50'), 30, 'PHYSICAL'),
            ("LiFePO4 Rechargeable Battery Pack", "BAT-LFP", "880192837404", cat_cmp, unit_pcs, Decimal('45.00'), Decimal('89.00'), 15, 'PHYSICAL'),
            ("Solid State Relay 40A", "SSR-40A", "880192837405", cat_cmp, unit_pcs, Decimal('14.00'), Decimal('29.00'), 20, 'PHYSICAL'),

            ("System Integration & Deployment", "SRV-INT", "", cat_srv, unit_hrs, Decimal('75.00'), Decimal('150.00'), 0, 'SERVICE'),
            ("Annual Maintenance Contract (Hardware)", "SRV-AMC", "", cat_srv, unit_set, Decimal('400.00'), Decimal('950.00'), 0, 'SERVICE'),
            ("Network Architecture Consulting", "SRV-NET", "", cat_srv, unit_hrs, Decimal('90.00'), Decimal('180.00'), 0, 'SERVICE'),
            ("Extended 3-Year Hardware Warranty", "SRV-WRNTY3", "", cat_srv, unit_set, Decimal('50.00'), Decimal('120.00'), 0, 'NON_STOCK'),
            ("Custom Enclosure 3D Printing Service", "SRV-3DPRINT", "", cat_srv, unit_pcs, Decimal('30.00'), Decimal('75.00'), 0, 'SERVICE'),
        ]

        products_list = []
        for name, sku, barcode, cat, unit, cost, price, reorder, ptype in sample_products:
            p, _ = Product.objects.get_or_create(organization=org, sku=sku, defaults={
                'name': name,
                'barcode': barcode,
                'category': cat,
                'unit': unit,
                'purchase_price': cost,
                'selling_price': price,
                'reorder_level': reorder,
                'product_type': ptype,
                'brand': 'StockFlow Brand',
                'description': f'High-grade commercial {name.lower()} built for reliable enterprise operation.'
            })
            products_list.append(p)

            if ptype == 'PHYSICAL':
                # Distribute stock across warehouses
                for wh in warehouses:
                    qty = random.randint(3, 40) if sku != 'PLC-X10' else random.randint(1, 4)
                    inv, created_inv = Inventory.objects.get_or_create(organization=org, product=p, warehouse=wh, defaults={'quantity': qty})
                    if created_inv:
                        StockMovement.objects.create(
                            organization=org,
                            product=p,
                            warehouse=wh,
                            movement_type='ADJUSTMENT',
                            quantity=qty,
                            quantity_before=0,
                            quantity_after=qty,
                            reference='OPENING_STOCK',
                            user=user,
                            notes='Initial stock balance'
                        )

        # 5. Suppliers (10)
        suppliers_data = [
            ("Apex Electronics Global Ltd.", "Hans Gruber", "hans@apexelectronics.de", "+49 30 9283 100", "Germany", "Net 30"),
            ("Pacific Semiconductor Corp", "Mei-Ling Chen", "sales@pacificsemi.tw", "+886 2 2700 8888", "Taiwan", "Net 15"),
            ("Nordic Industrial Hardware AS", "Lars Jensen", "info@nordicindustrial.no", "+47 22 10 99 88", "Norway", "Net 45"),
            ("Atlas Cable & Wire Co", "Robert Smith", "rsmith@atlascable.com", "+1 (312) 555-4321", "United States", "Net 30"),
            ("Shenzhen Tech Components", "Wei Zhang", "contact@sztechcomp.cn", "+86 755 8888 1234", "China", "Due on Receipt"),
            ("Britannia Networks UK Ltd", "Oliver Hughes", "oliver@britannianet.co.uk", "+44 20 7946 0912", "United Kingdom", "Net 30"),
            ("EuroSensors Technology GmbH", "Monika Weber", "mweber@eurosensors.at", "+43 1 505 1234", "Austria", "Net 30"),
            ("Maple Leaf Logistics & Supply", "Jean-Pierre Tremblay", "jptremblay@mapleleaf.ca", "+1 (416) 555-0188", "Canada", "Net 30"),
            ("Tokyo Precision Components", "Kenji Sato", "sato@tokyoprecision.jp", "+81 3 3500 1234", "Japan", "Net 60"),
            ("Aussie Industrial Solutions", "Sarah Jenkins", "s.jenkins@aussieindustrial.com.au", "+61 2 9876 5432", "Australia", "Net 30"),
        ]

        suppliers_list = []
        for name, contact, email, phone, country, terms in suppliers_data:
            sup, _ = Supplier.objects.get_or_create(organization=org, company_name=name, defaults={
                'contact_person': contact,
                'email': email,
                'phone': phone,
                'country': country,
                'payment_terms': terms,
                'currency': 'USD',
                'tax_id': f'TAX-{random.randint(100000, 999999)}',
                'address': f'100 Industrial Parkway, {country}'
            })
            suppliers_list.append(sup)

        # 6. Customers (10)
        customers_data = [
            ("Horizon Tech Solutions Inc", "David Miller", "dmiller@horizontech.com", "+1 (415) 555-9081", "United States", "Net 30"),
            ("London Digital Systems Ltd", "Emma Watson", "watson@londondigital.co.uk", "+44 20 7123 4567", "United Kingdom", "Net 30"),
            ("Bavaria Automation Solutions GmbH", "Klaus Fischer", "klaus@bavariaauto.de", "+49 89 4520 1100", "Germany", "Net 15"),
            ("Maple Wood Enterprises", "Marc Dubois", "mdubois@maplewood.ca", "+1 (514) 555-3211", "Canada", "Net 30"),
            ("Sydney Commercial Systems", "Chloe Bennett", "c.bennett@sydneycommercial.com.au", "+61 2 8123 9900", "Australia", "Net 30"),
            ("Alpine Energy & Control AG", "Reto Schneider", "reto@alpineenergy.ch", "+41 44 211 4400", "Switzerland", "Net 30"),
            ("Gulf Smart Systems WLL", "Tariq Al-Mansoor", "tariq@gulfsmart.ae", "+971 4 333 8899", "United Arab Emirates", "Net 30"),
            ("Singapore Robotics & Tech Pte", "Kevin Tan", "ktan@singaporerobotics.sg", "+65 6789 1234", "Singapore", "Net 30"),
            ("Nordic Retail Group AB", "Astrid Lindgren", "astrid@nordicretail.se", "+46 8 555 1212", "Sweden", "Net 45"),
            ("Metro Infrastructure Corp", "James Wilson", "jwilson@metroinfra.com", "+1 (202) 555-0144", "United States", "Due on Receipt"),
        ]

        customers_list = []
        for name, contact, email, phone, country, terms in customers_data:
            cust, _ = Customer.objects.get_or_create(organization=org, company_name=name, defaults={
                'contact_person': contact,
                'email': email,
                'phone': phone,
                'country': country,
                'payment_terms': terms,
                'currency': 'USD',
                'tax_id': f'CUST-TAX-{random.randint(100000, 999999)}',
                'address': f'500 Business Boulevard, Suite 200, {country}'
            })
            customers_list.append(cust)

        # 7. Generate 10 Purchase Orders & Bills & Receiving
        today = datetime.date.today()
        po_statuses = ['COMPLETED', 'PARTIALLY_RECEIVED', 'APPROVED', 'SENT', 'COMPLETED', 'COMPLETED', 'DRAFT']
        for i in range(1, 11):
            po_num = f"{org.po_prefix}{10020 + i}"
            sup = random.choice(suppliers_list)
            wh = random.choice(warehouses)
            status = po_statuses[(i - 1) % len(po_statuses)]
            order_dt = today - datetime.timedelta(days=random.randint(5, 75))

            po, created_po = PurchaseOrder.objects.get_or_create(organization=org, po_number=po_num, defaults={
                'supplier': sup,
                'warehouse': wh,
                'order_date': order_dt,
                'expected_delivery': order_dt + datetime.timedelta(days=7),
                'status': status,
                'created_by': user,
                'payment_terms': sup.payment_terms,
                'notes': f'Purchase Order generated for restock batch #{i}'
            })

            if created_po:
                # Add 2-4 items
                selected_prods = random.sample([p for p in products_list if p.product_type == 'PHYSICAL'], 3)
                for prod in selected_prods:
                    qty = random.randint(10, 50)
                    cost = prod.purchase_price
                    item = PurchaseOrderItem.objects.create(
                        purchase_order=po,
                        product=prod,
                        quantity=qty,
                        unit_cost=cost,
                        tax_rate=org.tax_rate,
                        discount=Decimal('0.00')
                    )
                    if status in ['COMPLETED', 'PARTIALLY_RECEIVED']:
                        recv_qty = qty if status == 'COMPLETED' else int(qty * 0.6)
                        item.received_quantity = recv_qty
                        item.save()

                        # Increase inventory
                        inv, _ = Inventory.objects.get_or_create(organization=org, product=prod, warehouse=wh, defaults={'quantity': 0})
                        before_q = inv.quantity
                        inv.quantity += recv_qty
                        inv.save()

                        StockMovement.objects.create(
                            organization=org,
                            product=prod,
                            warehouse=wh,
                            movement_type='PURCHASE',
                            quantity=recv_qty,
                            quantity_before=before_q,
                            quantity_after=inv.quantity,
                            reference=po_num,
                            user=user,
                            notes=f'Received against PO {po_num}'
                        )

                po.recalculate_totals()

                if status in ['COMPLETED', 'PARTIALLY_RECEIVED', 'APPROVED']:
                    bill_status = 'PAID' if i % 2 == 0 else ('OVERDUE' if i == 3 else 'OPEN')
                    bill_num = f"{org.bill_prefix}{20010 + i}"
                    PurchaseBill.objects.create(
                        organization=org,
                        supplier=sup,
                        purchase_order=po,
                        bill_number=bill_num,
                        bill_date=order_dt + datetime.timedelta(days=2),
                        due_date=order_dt + datetime.timedelta(days=32),
                        status=bill_status,
                        total_amount=po.total_amount,
                        paid_amount=po.total_amount if bill_status == 'PAID' else Decimal('0.00'),
                        notes=f'Bill generated from PO {po_num}'
                    )

        # 8. Generate 20 Invoices & Customer Payments
        inv_statuses = ['PAID', 'PAID', 'UNPAID', 'OVERDUE', 'PAID', 'PARTIALLY_PAID', 'UNPAID', 'PAID', 'OVERDUE', 'DRAFT']
        for i in range(1, 21):
            inv_num = f"{org.invoice_prefix}{9000 + i}"
            cust = random.choice(customers_list)
            wh = random.choice(warehouses)
            status = inv_statuses[(i - 1) % len(inv_statuses)]
            inv_dt = today - datetime.timedelta(days=random.randint(2, 85))
            due_dt = inv_dt + datetime.timedelta(days=30)

            if status == 'OVERDUE' and due_dt > today:
                due_dt = today - datetime.timedelta(days=random.randint(5, 20))

            inv, created_inv = Invoice.objects.get_or_create(organization=org, invoice_number=inv_num, defaults={
                'customer': cust,
                'warehouse': wh,
                'invoice_date': inv_dt,
                'due_date': due_dt,
                'status': status,
                'payment_terms': cust.payment_terms,
                'created_by': user,
                'notes': 'Thank you for your business!',
                'terms': 'Payment due within 30 days. Standard commercial interest applies to overdue balances.'
            })

            if created_inv:
                selected_prods = random.sample(products_list, random.randint(2, 4))
                sub = Decimal('0.00')
                tax_tot = Decimal('0.00')

                for prod in selected_prods:
                    qty = random.randint(2, 12)
                    price = prod.selling_price
                    item = InvoiceItem.objects.create(
                        invoice=inv,
                        product=prod,
                        description=f"{prod.name} ({prod.sku})",
                        quantity=qty,
                        unit_price=price,
                        tax_rate=org.tax_rate,
                        discount=Decimal('0.00')
                    )
                    line_sub = Decimal(qty) * price
                    sub += line_sub
                    tax_tot += line_sub * (org.tax_rate / Decimal('100.0'))

                    if status in ['PAID', 'UNPAID', 'PARTIALLY_PAID', 'OVERDUE'] and prod.product_type == 'PHYSICAL':
                        # Deduct inventory
                        inv_level, _ = Inventory.objects.get_or_create(organization=org, product=prod, warehouse=wh, defaults={'quantity': 50})
                        before_q = inv_level.quantity
                        inv_level.quantity = max(0, inv_level.quantity - qty)
                        inv_level.save()

                        StockMovement.objects.create(
                            organization=org,
                            product=prod,
                            warehouse=wh,
                            movement_type='SALE',
                            quantity=-qty,
                            quantity_before=before_q,
                            quantity_after=inv_level.quantity,
                            reference=inv_num,
                            user=user,
                            notes=f'Issued on Invoice {inv_num}'
                        )

                inv.subtotal = sub
                inv.tax_amount = tax_tot
                inv.total_amount = sub + tax_tot

                if status == 'PAID':
                    inv.paid_amount = inv.total_amount
                    Payment.objects.create(
                        organization=org,
                        payment_type='RECEIVABLE',
                        customer=cust,
                        invoice=inv,
                        payment_number=f"PAY-{1000 + i}",
                        payment_date=inv_dt + datetime.timedelta(days=10),
                        amount=inv.total_amount,
                        currency=org.currency_code,
                        payment_method='Bank Transfer',
                        reference=f'WIRE-{random.randint(10000, 99999)}',
                        created_by=user,
                        notes='Full payment received via bank transfer'
                    )
                elif status == 'PARTIALLY_PAID':
                    partial = inv.total_amount * Decimal('0.5')
                    inv.paid_amount = partial
                    Payment.objects.create(
                        organization=org,
                        payment_type='RECEIVABLE',
                        customer=cust,
                        invoice=inv,
                        payment_number=f"PAY-{1000 + i}",
                        payment_date=inv_dt + datetime.timedelta(days=5),
                        amount=partial,
                        currency=org.currency_code,
                        payment_method='Credit Card',
                        reference=f'CC-{random.randint(10000, 99999)}',
                        created_by=user,
                        notes='50% deposit received'
                    )
                else:
                    inv.paid_amount = Decimal('0.00')

                inv.save()

        # 9. Create Notifications & Audit Logs
        Notification.objects.get_or_create(
            organization=org,
            title='Low Stock Alert: Programmable Logic Controller (PLC)',
            defaults={
                'notification_type': 'LOW_STOCK',
                'message': 'Product PLC-X10 stock level has fallen below the reorder threshold (5 units remaining).',
                'link': '/inventory/products/',
                'is_read': False
            }
        )

        Notification.objects.get_or_create(
            organization=org,
            title='Overdue Invoices Requiring Attention',
            defaults={
                'notification_type': 'INVOICE_OVERDUE',
                'message': 'You have 3 invoices past due totaling over $12,400 in receivables.',
                'link': '/finance/receivables/',
                'is_read': False
            }
        )

        AuditLog.objects.create(
            organization=org,
            user=user,
            action='Demo Data Initialized',
            object_type='Organization',
            object_repr=org.name,
            details='Seeded 25 products, 3 warehouses, 10 suppliers, 10 customers, 20 invoices, and 10 POs.'
        )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded StockFlow demo data for organization: {org.name}!"))
