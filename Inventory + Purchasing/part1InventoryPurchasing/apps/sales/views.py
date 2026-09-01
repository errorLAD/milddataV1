from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
import datetime

from apps.sales.models import Customer, SalesQuote, SalesQuoteItem, SalesOrder, SalesOrderItem, Invoice, InvoiceItem
from apps.inventory.models import Product, Warehouse, Inventory, StockMovement
from apps.finance.models import Payment
from apps.core.models import AuditLog, Notification

# --- CUSTOMERS ---
@login_required
def customer_list_view(request):
    org = request.organization
    customers = Customer.objects.filter(organization=org)
    q = request.GET.get('q', '').strip()
    if q:
        customers = customers.filter(Q(company_name__icontains=q) | Q(contact_person__icontains=q) | Q(email__icontains=q))

    context = {
        'customers': customers,
        'q': q,
        'total_customers': customers.count(),
    }
    return render(request, 'sales/customer_list.html', context)

@login_required
def customer_create_view(request):
    org = request.organization
    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        contact_person = request.POST.get('contact_person', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        country = request.POST.get('country', 'United States')
        address = request.POST.get('address', '').strip()
        payment_terms = request.POST.get('payment_terms', 'Net 30')
        tax_id = request.POST.get('tax_id', '').strip()

        if company_name:
            cust = Customer.objects.create(
                organization=org,
                company_name=company_name,
                contact_person=contact_person,
                email=email,
                phone=phone,
                country=country,
                address=address,
                payment_terms=payment_terms,
                currency=org.currency_code,
                tax_id=tax_id
            )
            AuditLog.objects.create(
                organization=org,
                user=request.user,
                action='Customer Created',
                object_type='Customer',
                object_repr=cust.company_name
            )
            messages.success(request, f"Customer '{cust.company_name}' created.")
            return redirect('customer_detail', customer_id=cust.id)

    return redirect('customer_list')

@login_required
def customer_detail_view(request, customer_id):
    org = request.organization
    customer = get_object_or_404(Customer, id=customer_id, organization=org)

    quotes = SalesQuote.objects.filter(customer=customer)
    orders = SalesOrder.objects.filter(customer=customer)
    invoices = Invoice.objects.filter(customer=customer)
    payments = Payment.objects.filter(customer=customer, payment_type='RECEIVABLE')

    context = {
        'customer': customer,
        'quotes': quotes,
        'orders': orders,
        'invoices': invoices,
        'payments': payments,
    }
    return render(request, 'sales/customer_detail.html', context)

# --- QUOTES & ORDERS ---
@login_required
def quote_list_view(request):
    org = request.organization
    quotes = SalesQuote.objects.filter(organization=org)
    return render(request, 'sales/quote_list.html', {'quotes': quotes})

@login_required
def quote_create_view(request):
    org = request.organization
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        quote_date = request.POST.get('quote_date') or datetime.date.today().strftime('%Y-%m-%d')
        expiry_date = request.POST.get('expiry_date')
        notes = request.POST.get('notes', '').strip()
        terms = request.POST.get('terms', '').strip()

        customer = get_object_or_404(Customer, id=customer_id, organization=org)
        last_q = SalesQuote.objects.filter(organization=org).order_by('-id').first()
        seq = (last_q.id + 1) if last_q else 101
        q_num = f"{org.quote_prefix}{seq}"

        with transaction.atomic():
            quote = SalesQuote.objects.create(
                organization=org,
                customer=customer,
                quote_number=q_num,
                quote_date=quote_date,
                expiry_date=expiry_date if expiry_date else None,
                status='DRAFT',
                notes=notes,
                terms=terms,
                created_by=request.user
            )

            product_ids = request.POST.getlist('product_id[]')
            quantities = request.POST.getlist('quantity[]')
            prices = request.POST.getlist('unit_price[]')

            sub = Decimal('0.00')
            tax_tot = Decimal('0.00')

            for pid, qty_str, price_str in zip(product_ids, quantities, prices):
                if pid and qty_str:
                    prod = Product.objects.filter(id=pid, organization=org).first()
                    if prod:
                        qty = int(qty_str or '1')
                        price = Decimal(price_str or '0.00')
                        line_tot = Decimal(qty) * price
                        sub += line_tot
                        line_tax = line_tot * (org.tax_rate / Decimal('100.0'))
                        tax_tot += line_tax

                        SalesQuoteItem.objects.create(
                            quote=quote,
                            product=prod,
                            quantity=qty,
                            unit_price=price,
                            tax_rate=org.tax_rate,
                            total=line_tot + line_tax
                        )

            quote.subtotal = sub
            quote.tax_amount = tax_tot
            quote.total_amount = sub + tax_tot
            quote.save()

            messages.success(request, f"Sales Quote {quote.quote_number} created.")
            return redirect('quote_list')

    customers = Customer.objects.filter(organization=org)
    products = Product.objects.filter(organization=org, is_archived=False)
    return render(request, 'sales/quote_form.html', {'customers': customers, 'products': products})

@login_required
def quote_convert_view(request, quote_id):
    org = request.organization
    quote = get_object_or_404(SalesQuote, id=quote_id, organization=org)

    wh = Warehouse.objects.filter(organization=org, is_primary=True).first() or Warehouse.objects.filter(organization=org).first()
    last_inv = Invoice.objects.filter(organization=org).order_by('-id').first()
    seq = (last_inv.id + 1) if last_inv else 1001
    inv_num = f"{org.invoice_prefix}{seq}"

    with transaction.atomic():
        invoice = Invoice.objects.create(
            organization=org,
            customer=quote.customer,
            warehouse=wh,
            invoice_number=inv_num,
            invoice_date=datetime.date.today(),
            due_date=datetime.date.today() + datetime.timedelta(days=30),
            status='UNPAID',
            payment_terms=quote.customer.payment_terms,
            notes=quote.notes,
            terms=quote.terms,
            subtotal=quote.subtotal,
            tax_amount=quote.tax_amount,
            total_amount=quote.total_amount,
            created_by=request.user
        )

        for q_item in quote.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                product=q_item.product,
                description=q_item.product.name,
                quantity=q_item.quantity,
                unit_price=q_item.unit_price,
                tax_rate=q_item.tax_rate,
                total=q_item.total
            )

            # Deduct inventory
            if q_item.product.product_type == 'PHYSICAL' and wh:
                inv_level, _ = Inventory.objects.get_or_create(organization=org, product=q_item.product, warehouse=wh, defaults={'quantity': 0})
                before_q = inv_level.quantity
                inv_level.quantity = max(0, inv_level.quantity - q_item.quantity)
                inv_level.save()

                StockMovement.objects.create(
                    organization=org,
                    product=q_item.product,
                    warehouse=wh,
                    movement_type='SALE',
                    quantity=-q_item.quantity,
                    quantity_before=before_q,
                    quantity_after=inv_level.quantity,
                    reference=invoice.invoice_number,
                    user=request.user,
                    notes=f"Converted from Quote {quote.quote_number}"
                )

        quote.status = 'CONVERTED'
        quote.save()

        messages.success(request, f"Quote {quote.quote_number} converted to Invoice {invoice.invoice_number}.")
        return redirect('invoice_detail', invoice_id=invoice.id)

# --- INVOICES ---
@login_required
def invoice_list_view(request):
    org = request.organization
    invoices = Invoice.objects.filter(organization=org)

    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    q = request.GET.get('q', '').strip()
    if q:
        invoices = invoices.filter(Q(invoice_number__icontains=q) | Q(customer__company_name__icontains=q))

    customers = Customer.objects.filter(organization=org)

    context = {
        'invoices': invoices,
        'customers': customers,
        'selected_status': status_filter,
        'q': q,
    }
    return render(request, 'sales/invoice_list.html', context)

@login_required
def invoice_create_view(request):
    org = request.organization
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        warehouse_id = request.POST.get('warehouse_id')
        invoice_date_str = request.POST.get('invoice_date') or datetime.date.today().strftime('%Y-%m-%d')
        due_date_str = request.POST.get('due_date')
        notes = request.POST.get('notes', '').strip()
        terms = request.POST.get('terms', '').strip()

        customer = get_object_or_404(Customer, id=customer_id, organization=org)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id, organization=org) if warehouse_id else Warehouse.objects.filter(organization=org, is_primary=True).first()

        last_inv = Invoice.objects.filter(organization=org).order_by('-id').first()
        seq = (last_inv.id + 1) if last_inv else 1001
        inv_number = f"{org.invoice_prefix}{seq}"

        with transaction.atomic():
            inv = Invoice.objects.create(
                organization=org,
                customer=customer,
                warehouse=warehouse,
                invoice_number=inv_number,
                invoice_date=invoice_date_str,
                due_date=due_date_str if due_date_str else (datetime.datetime.strptime(invoice_date_str, '%Y-%m-%d').date() + datetime.timedelta(days=30)),
                status='UNPAID',
                payment_terms=customer.payment_terms,
                notes=notes,
                terms=terms,
                created_by=request.user
            )

            product_ids = request.POST.getlist('product_id[]')
            quantities = request.POST.getlist('quantity[]')
            prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')

            sub = Decimal('0.00')
            tax_tot = Decimal('0.00')

            for pid, qty_str, price_str, disc_str in zip(product_ids, quantities, prices, discounts):
                if pid and qty_str:
                    prod = Product.objects.filter(id=pid, organization=org).first()
                    if prod:
                        qty = int(qty_str or '1')
                        price = Decimal(price_str or '0.00')
                        disc = Decimal(disc_str or '0.00')

                        line_sub = (Decimal(qty) * price) - disc
                        sub += line_sub
                        line_tax = line_sub * (org.tax_rate / Decimal('100.0'))
                        tax_tot += line_tax

                        InvoiceItem.objects.create(
                            invoice=inv,
                            product=prod,
                            description=prod.name,
                            quantity=qty,
                            unit_price=price,
                            discount=disc,
                            tax_rate=org.tax_rate,
                            total=line_sub + line_tax
                        )

                        # Automatic Inventory Decrease
                        if prod.product_type == 'PHYSICAL' and warehouse:
                            inv_level, _ = Inventory.objects.get_or_create(organization=org, product=prod, warehouse=warehouse, defaults={'quantity': 0})
                            before_q = inv_level.quantity
                            inv_level.quantity = max(0, inv_level.quantity - qty)
                            inv_level.save()

                            StockMovement.objects.create(
                                organization=org,
                                product=prod,
                                warehouse=warehouse,
                                movement_type='SALE',
                                quantity=-qty,
                                quantity_before=before_q,
                                quantity_after=inv_level.quantity,
                                reference=inv_number,
                                user=request.user,
                                notes=f"Issued on Invoice {inv_number}"
                            )

            inv.subtotal = sub
            inv.tax_amount = tax_tot
            inv.total_amount = sub + tax_tot
            inv.save()

            AuditLog.objects.create(
                organization=org,
                user=request.user,
                action='Invoice Created',
                object_type='Invoice',
                object_repr=inv.invoice_number
            )

        messages.success(request, f"Invoice {inv.invoice_number} created and inventory updated.")
        return redirect('invoice_detail', invoice_id=inv.id)

    customers = Customer.objects.filter(organization=org)
    warehouses = Warehouse.objects.filter(organization=org)
    products = Product.objects.filter(organization=org, is_archived=False)

    return render(request, 'sales/invoice_form.html', {
        'customers': customers,
        'warehouses': warehouses,
        'products': products,
    })

@login_required
def invoice_detail_view(request, invoice_id):
    org = request.organization
    invoice = get_object_or_404(Invoice, id=invoice_id, organization=org)
    payments = Payment.objects.filter(invoice=invoice)

    context = {
        'invoice': invoice,
        'payments': payments,
    }
    return render(request, 'sales/invoice_detail.html', context)
