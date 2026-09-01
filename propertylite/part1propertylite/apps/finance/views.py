from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import RentInvoice, Payment, Expense
from apps.properties.models import Property
from apps.leases.models import Lease
from apps.core.models import AuditLog, Notification, User
from apps.core.utils.security import guest_restricted
import datetime

@login_required
def rent_collection(request):
    org = request.user.organization
    invoices = RentInvoice.objects.filter(organization=org)
    payments = Payment.objects.filter(organization=org)

    expected = sum(inv.total_due for inv in invoices)
    collected = sum(inv.total_paid for inv in invoices)
    outstanding = expected - collected
    overdue = sum(inv.total_due - inv.total_paid for inv in invoices.filter(status=RentInvoice.STATUS_OVERDUE))

    return render(request, 'finance/rent_collection.html', {
        'invoices': invoices,
        'payments': payments,
        'expected': expected,
        'collected': collected,
        'outstanding': outstanding,
        'overdue': overdue,
    })

@login_required
@guest_restricted
def payment_record(request, invoice_pk):
    org = request.user.organization
    invoice = get_object_or_404(RentInvoice, id=invoice_pk, organization=org)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        method = request.POST.get('payment_method')
        ref_no = request.POST.get('reference_number')
        p_date = request.POST.get('payment_date') or datetime.date.today()

        payment = Payment.objects.create(
            organization=org,
            invoice=invoice,
            tenant=invoice.tenant,
            amount=amount,
            payment_date=p_date,
            payment_method=method,
            reference_number=ref_no,
            status=Payment.STATUS_COMPLETED
        )

        # Update invoice status
        if invoice.total_paid >= invoice.total_due:
            invoice.status = RentInvoice.STATUS_PAID
        elif invoice.total_paid > 0:
            invoice.status = RentInvoice.STATUS_PARTIALLY_PAID
        invoice.save()

        Notification.objects.create(
            organization=org,
            recipient=invoice.tenant,
            title="Rent Payment Recorded",
            message=f"Payment of ${amount} for Invoice #{invoice.invoice_number} received. Thank you!",
            notification_type=Notification.TYPE_PAYMENT
        )

        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action=f"Recorded Payment ${amount} for Invoice #{invoice.invoice_number}",
            entity_type="Payment",
            entity_id=str(payment.id)
        )

        messages.success(request, f"Payment of ${amount} recorded successfully!")
        return redirect('rent_collection')

    return render(request, 'finance/payment_form.html', {'invoice': invoice})

@login_required
def expense_list(request):
    org = request.user.organization
    expenses = Expense.objects.filter(organization=org)
    properties = Property.objects.filter(organization=org)
    
    total_expenses = sum(exp.amount for exp in expenses)

    return render(request, 'finance/expense_list.html', {
        'expenses': expenses,
        'properties': properties,
        'categories': Expense.CATEGORY_CHOICES,
        'total_expenses': total_expenses
    })

@login_required
@guest_restricted
def expense_create(request):
    org = request.user.organization
    
    if request.method == 'POST':
        property_id = request.POST.get('property')
        category = request.POST.get('category')
        amount = request.POST.get('amount')
        date = request.POST.get('date') or datetime.date.today()
        vendor_name = request.POST.get('vendor_name')
        description = request.POST.get('description')

        prop = get_object_or_404(Property, id=property_id, organization=org)

        expense = Expense.objects.create(
            organization=org,
            property=prop,
            category=category,
            amount=amount,
            date=date,
            vendor_name=vendor_name,
            description=description
        )

        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action=f"Recorded Expense ${amount} for {prop.name}",
            entity_type="Expense",
            entity_id=str(expense.id)
        )

        messages.success(request, f"Expense of ${amount} recorded for {prop.name}!")
        return redirect('expense_list')

    return redirect('expense_list')
