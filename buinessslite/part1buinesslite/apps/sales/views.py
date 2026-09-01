from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from apps.sales.models import (
    Customer, Quote, QuoteItem, QuoteStatus,
    SalesOrder, SalesOrderItem, OrderStatus,
    Invoice, InvoiceItem, InvoiceStatus, Payment, PaymentMethod, Return
)
from apps.inventory.models import Product, StockMovement, MovementType
from apps.core.models import AuditLog, Notification, NotificationType

@login_required
def customer_list_view(request):
    org = request.organization
    customers = Customer.objects.filter(organization=org)
    return render(request, 'sales/customer_list.html', {'customers': customers})

@login_required
def customer_create_view(request):
    org = request.organization
    if request.method == 'POST':
        c = Customer.objects.create(
            organization=org,
            company_name=request.POST.get('company_name'),
            contact_person=request.POST.get('contact_person'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            country=request.POST.get('country', org.country),
            payment_terms=request.POST.get('payment_terms', 'Net 30')
        )
        AuditLog.objects.create(organization=org, user=request.user, action="Customer Created", model_name="Customer", record_id=str(c.id), details=f"Customer {c.company_name} created.")
        return redirect('customer_list')
    return render(request, 'sales/customer_form.html')

@login_required
def customer_detail_view(request, cust_id):
    org = request.organization
    customer = get_object_or_404(Customer, id=cust_id, organization=org)
    invoices = Invoice.objects.filter(customer=customer)
    payments = Payment.objects.filter(customer=customer)
    orders = SalesOrder.objects.filter(customer=customer)
    return render(request, 'sales/customer_detail.html', {'customer': customer, 'invoices': invoices, 'payments': payments, 'orders': orders})

@login_required
def quote_list_view(request):
    org = request.organization
    quotes = Quote.objects.filter(organization=org)
    return render(request, 'sales/quote_list.html', {'quotes': quotes})

@login_required
def quote_create_view(request):
    org = request.organization
    if request.method == 'POST':
        cust = get_object_or_404(Customer, id=request.POST.get('customer_id'), organization=org)
        q_num = f"{org.quote_prefix}{Quote.objects.filter(organization=org).count() + 1001}"
        quote = Quote.objects.create(
            organization=org, quote_number=q_num, customer=cust,
            date=request.POST.get('date') or timezone.now().date(),
            expiry_date=request.POST.get('expiry_date') or None
        )
        
        prod_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')
        prices = request.POST.getlist('unit_price')
        
        total = 0.0
        for i in range(len(prod_ids)):
            if prod_ids[i]:
                prod = Product.objects.get(id=prod_ids[i], organization=org)
                qty = int(quantities[i])
                pr = float(prices[i])
                line = qty * pr
                total += line
                QuoteItem.objects.create(quote=quote, product=prod, description=prod.name, quantity=qty, unit_price=pr, line_total=line)
        quote.total_amount = total
        quote.save()
        AuditLog.objects.create(organization=org, user=request.user, action="Quote Created", model_name="Quote", record_id=str(quote.id), details=f"Quote {quote.quote_number} created.")
        return redirect('quote_list')

    customers = Customer.objects.filter(organization=org)
    products = Product.objects.filter(organization=org)
    return render(request, 'sales/quote_form.html', {'customers': customers, 'products': products})

@login_required
def convert_quote_to_order(request, quote_id):
    org = request.organization
    quote = get_object_or_404(Quote, id=quote_id, organization=org)
    order_num = f"{org.order_prefix}{SalesOrder.objects.filter(organization=org).count() + 1001}"
    
    order = SalesOrder.objects.create(
        organization=org, order_number=order_num, customer=quote.customer,
        date=timezone.now().date(), status=OrderStatus.CONFIRMED, total_amount=quote.total_amount
    )
    for q_item in quote.items.all():
        SalesOrderItem.objects.create(
            sales_order=order, product=q_item.product, description=q_item.description,
            quantity=q_item.quantity, unit_price=q_item.unit_price, line_total=q_item.line_total
        )
    quote.status = QuoteStatus.CONVERTED
    quote.save()
    AuditLog.objects.create(organization=org, user=request.user, action="Quote Converted", model_name="SalesOrder", record_id=str(order.id), details=f"Quote {quote.quote_number} converted to Order {order.order_number}.")
    return redirect('sales_order_list')

@login_required
def sales_order_list_view(request):
    org = request.organization
    orders = SalesOrder.objects.filter(organization=org)
    return render(request, 'sales/order_list.html', {'orders': orders})

@login_required
def invoice_list_view(request):
    org = request.organization
    invoices = Invoice.objects.filter(organization=org)
    return render(request, 'sales/invoice_list.html', {'invoices': invoices})

@login_required
def invoice_create_view(request):
    org = request.organization
    if request.method == 'POST':
        cust = get_object_or_404(Customer, id=request.POST.get('customer_id'), organization=org)
        inv_num = f"{org.invoice_prefix}{Invoice.objects.filter(organization=org).count() + 1001}"
        date_val = request.POST.get('date') or timezone.now().date()
        due_val = request.POST.get('due_date') or (timezone.now().date() + timedelta(days=30))
        
        inv = Invoice.objects.create(
            organization=org, invoice_number=inv_num, customer=cust,
            date=date_val, due_date=due_val, status=InvoiceStatus.UNPAID
        )
        
        prod_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')
        prices = request.POST.getlist('unit_price')
        
        total = 0.0
        for i in range(len(prod_ids)):
            if prod_ids[i]:
                prod = Product.objects.get(id=prod_ids[i], organization=org)
                qty = int(quantities[i])
                pr = float(prices[i])
                line = qty * pr
                total += line
                InvoiceItem.objects.create(invoice=inv, product=prod, description=prod.name, quantity=qty, unit_price=pr, line_total=line)
                
                # Stock deduction for physical goods
                if prod.product_type == 'PHYSICAL':
                    prod.stock_quantity -= qty
                    prod.save()
                    StockMovement.objects.create(
                        organization=org, product=prod, quantity_change=-qty,
                        movement_type=MovementType.STOCK_OUT, reference=f"Invoice: {inv.invoice_number}", created_by=request.user
                    )
        inv.total_amount = total
        inv.save()
        AuditLog.objects.create(organization=org, user=request.user, action="Invoice Created", model_name="Invoice", record_id=str(inv.id), details=f"Invoice {inv.invoice_number} created for {cust.company_name}.")
        return redirect('invoice_detail', inv_id=inv.id)

    customers = Customer.objects.filter(organization=org)
    products = Product.objects.filter(organization=org)
    return render(request, 'sales/invoice_form.html', {'customers': customers, 'products': products})

@login_required
def invoice_detail_view(request, inv_id):
    org = request.organization
    inv = get_object_or_404(Invoice, id=inv_id, organization=org)
    items = inv.items.all()
    payments = inv.payments.all()
    return render(request, 'sales/invoice_detail.html', {'inv': inv, 'items': items, 'payments': payments})

@login_required
def record_payment_view(request, inv_id):
    org = request.organization
    inv = get_object_or_404(Invoice, id=inv_id, organization=org)
    if request.method == 'POST':
        amt = float(request.POST.get('amount', 0.0))
        method = request.POST.get('payment_method', PaymentMethod.BANK_TRANSFER)
        ref = request.POST.get('reference', '')
        
        pay_num = f"PAY-{Payment.objects.filter(organization=org).count() + 1001}"
        Payment.objects.create(
            organization=org, invoice=inv, customer=inv.customer, payment_number=pay_num,
            date=request.POST.get('date') or timezone.now().date(), amount=amt, payment_method=method, reference=ref
        )
        inv.paid_amount += amt
        if inv.paid_amount >= inv.total_amount:
            inv.status = InvoiceStatus.PAID
        else:
            inv.status = InvoiceStatus.PARTIAL
        inv.save()
        
        Notification.objects.create(
            organization=org, title="Payment Received", message=f"Received {org.currency_symbol}{amt} for invoice {inv.invoice_number}.",
            notification_type=NotificationType.PAYMENT_RECEIVED, link=f"/sales/invoices/{inv.id}/"
        )
        AuditLog.objects.create(organization=org, user=request.user, action="Payment Recorded", model_name="Payment", record_id=str(inv.id), details=f"Payment of {amt} recorded for invoice {inv.invoice_number}.")
        return redirect('invoice_detail', inv_id=inv.id)
    return render(request, 'sales/record_payment_form.html', {'inv': inv, 'methods': PaymentMethod.choices})

@login_required
def invoice_pdf_view(request, inv_id):
    org = request.organization
    inv = get_object_or_404(Invoice, id=inv_id, organization=org)
    items = inv.items.all()
    return render(request, 'sales/invoice_pdf.html', {'inv': inv, 'items': items})

@login_required
def payment_receipt_view(request, pay_id):
    org = request.organization
    payment = get_object_or_404(Payment, id=pay_id, organization=org)
    return render(request, 'sales/payment_receipt.html', {'payment': payment})
