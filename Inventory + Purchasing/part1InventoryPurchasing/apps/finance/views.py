from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
import datetime

from apps.sales.models import Invoice, Customer
from apps.purchasing.models import PurchaseBill, Supplier
from apps.finance.models import Payment
from apps.inventory.models import StockMovement, Product
from apps.core.models import AuditLog

@login_required
def receivables_view(request):
    org = request.organization
    open_invoices = Invoice.objects.filter(organization=org, status__in=['UNPAID', 'PARTIALLY_PAID', 'OVERDUE'])

    today = datetime.date.today()

    total_outstanding = Decimal('0.00')
    due_today = Decimal('0.00')
    due_soon = Decimal('0.00')
    overdue = Decimal('0.00')

    aging_current = Decimal('0.00') # 1-30 days
    aging_30_60 = Decimal('0.00') # 31-60 days
    aging_60_90 = Decimal('0.00') # 61-90 days
    aging_90_plus = Decimal('0.00') # 90+ days

    for inv in open_invoices:
        bal = inv.remaining_balance
        total_outstanding += bal

        if inv.due_date < today:
            overdue += bal
            inv.status = 'OVERDUE'
            inv.save()
            days_overdue = (today - inv.due_date).days
            if days_overdue <= 30:
                aging_current += bal
            elif days_overdue <= 60:
                aging_30_60 += bal
            elif days_overdue <= 90:
                aging_60_90 += bal
            else:
                aging_90_plus += bal
        elif inv.due_date == today:
            due_today += bal
            aging_current += bal
        else:
            due_soon += bal
            aging_current += bal

    customers = Customer.objects.filter(organization=org)
    payment_methods = Payment.PAYMENT_METHODS

    context = {
        'invoices': open_invoices,
        'customers': customers,
        'payment_methods': payment_methods,
        'total_outstanding': total_outstanding,
        'due_today': due_today,
        'due_soon': due_soon,
        'overdue': overdue,
        'aging_current': aging_current,
        'aging_30_60': aging_30_60,
        'aging_60_90': aging_60_90,
        'aging_90_plus': aging_90_plus,
    }
    return render(request, 'finance/receivables.html', context)

@login_required
def payables_view(request):
    org = request.organization
    open_bills = PurchaseBill.objects.filter(organization=org, status__in=['OPEN', 'PARTIALLY_PAID', 'OVERDUE'])

    today = datetime.date.today()

    total_payable = Decimal('0.00')
    due_soon = Decimal('0.00')
    overdue = Decimal('0.00')

    for bill in open_bills:
        bal = bill.remaining_balance
        total_payable += bal
        if bill.due_date < today:
            overdue += bal
            bill.status = 'OVERDUE'
            bill.save()
        else:
            due_soon += bal

    suppliers = Supplier.objects.filter(organization=org)
    payment_methods = Payment.PAYMENT_METHODS

    context = {
        'bills': open_bills,
        'suppliers': suppliers,
        'payment_methods': payment_methods,
        'total_payable': total_payable,
        'due_soon': due_soon,
        'overdue': overdue,
    }
    return render(request, 'finance/payables.html', context)

@login_required
def record_payment_view(request):
    org = request.organization
    if request.method == 'POST':
        payment_type = request.POST.get('payment_type', 'RECEIVABLE')
        customer_id = request.POST.get('customer_id')
        supplier_id = request.POST.get('supplier_id')
        invoice_id = request.POST.get('invoice_id')
        bill_id = request.POST.get('bill_id')

        amount = Decimal(request.POST.get('amount', '0.00') or '0.00')
        payment_date = request.POST.get('payment_date') or datetime.date.today().strftime('%Y-%m-%d')
        payment_method = request.POST.get('payment_method', 'Bank Transfer')
        reference = request.POST.get('reference', '').strip()
        notes = request.POST.get('notes', '').strip()

        with transaction.atomic():
            last_p = Payment.objects.filter(organization=org).order_by('-id').first()
            seq = (last_p.id + 1) if last_p else 5001
            p_number = f"PAY-{seq}"

            customer = Customer.objects.filter(id=customer_id, organization=org).first() if customer_id else None
            supplier = Supplier.objects.filter(id=supplier_id, organization=org).first() if supplier_id else None
            invoice = Invoice.objects.filter(id=invoice_id, organization=org).first() if invoice_id else None
            bill = PurchaseBill.objects.filter(id=bill_id, organization=org).first() if bill_id else None

            if invoice:
                customer = invoice.customer

            if bill:
                supplier = bill.supplier

            payment = Payment.objects.create(
                organization=org,
                payment_type=payment_type,
                customer=customer,
                supplier=supplier,
                invoice=invoice,
                bill=bill,
                payment_number=p_number,
                payment_date=payment_date,
                amount=amount,
                currency=org.currency_code,
                payment_method=payment_method,
                reference=reference,
                notes=notes,
                created_by=request.user
            )

            # Update Invoice paid amount & status
            if invoice:
                invoice.paid_amount += amount
                if invoice.paid_amount >= invoice.total_amount:
                    invoice.status = 'PAID'
                else:
                    invoice.status = 'PARTIALLY_PAID'
                invoice.save()

            # Update PurchaseBill paid amount & status
            if bill:
                bill.paid_amount += amount
                if bill.paid_amount >= bill.total_amount:
                    bill.status = 'PAID'
                else:
                    bill.status = 'PARTIALLY_PAID'
                bill.save()

            AuditLog.objects.create(
                organization=org,
                user=request.user,
                action=f"Payment Recorded ({payment_type})",
                object_type='Payment',
                object_repr=f"{p_number} ({org.currency_symbol}{amount})"
            )

        messages.success(request, f"Payment {p_number} recorded successfully.")

        if payment_type == 'RECEIVABLE':
            return redirect('receivables')
        return redirect('payables')

    return redirect('receivables')

@login_required
def profitability_view(request):
    org = request.organization
    invoices = Invoice.objects.filter(organization=org, status__in=['UNPAID', 'PARTIALLY_PAID', 'PAID', 'OVERDUE'])

    total_revenue = Decimal('0.00')
    total_cogs = Decimal('0.00')

    for inv in invoices:
        for item in inv.items.all():
            total_revenue += item.total
            # COGS = quantity * purchase_price
            cogs_unit = item.product.purchase_price
            total_cogs += Decimal(item.quantity) * cogs_unit

    gross_profit = total_revenue - total_cogs
    gross_margin_pct = (gross_profit / total_revenue * Decimal('100.0')) if total_revenue > 0 else Decimal('0.00')

    context = {
        'total_revenue': total_revenue,
        'total_cogs': total_cogs,
        'gross_profit': gross_profit,
        'gross_margin_pct': round(gross_margin_pct, 1),
    }
    return render(request, 'finance/profitability.html', context)
