from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta

from apps.finance.models import Expense, ExpenseCategory
from apps.sales.models import Invoice, InvoiceStatus, Customer
from apps.purchasing.models import PurchaseOrder, POStatus, Supplier
from apps.core.models import AuditLog

@login_required
def expense_list_view(request):
    org = request.organization
    expenses = Expense.objects.filter(organization=org)
    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or 0.00
    return render(request, 'finance/expense_list.html', {'expenses': expenses, 'total_expense': total_expense})

@login_required
def expense_create_view(request):
    org = request.organization
    if request.method == 'POST':
        cat_id = request.POST.get('category_id')
        category = ExpenseCategory.objects.filter(id=cat_id, organization=org).first() if cat_id else None
        
        e = Expense.objects.create(
            organization=org,
            title=request.POST.get('title'),
            amount=float(request.POST.get('amount', 0.0)),
            category=category,
            date=request.POST.get('date') or timezone.now().date(),
            payment_method=request.POST.get('payment_method', 'Bank Transfer'),
            vendor=request.POST.get('vendor', '')
        )
        AuditLog.objects.create(organization=org, user=request.user, action="Expense Added", model_name="Expense", record_id=str(e.id), details=f"Expense '{e.title}' ({org.currency_symbol}{e.amount}) added.")
        return redirect('expense_list')

    categories = ExpenseCategory.objects.filter(organization=org)
    return render(request, 'finance/expense_form.html', {'categories': categories})

@login_required
def receivables_view(request):
    org = request.organization
    today = timezone.now().date()
    
    unpaid_invoices = Invoice.objects.filter(organization=org).exclude(status__in=[InvoiceStatus.PAID, InvoiceStatus.VOID])
    
    total_outstanding = 0.0
    current_amount = 0.0
    days_1_30 = 0.0
    days_31_60 = 0.0
    days_61_90 = 0.0
    days_90_plus = 0.0

    aging_invoices = []
    for inv in unpaid_invoices:
        rem = float(inv.remaining_amount)
        total_outstanding += rem
        days_overdue = (today - inv.due_date).days

        if days_overdue <= 0:
            current_amount += rem
            bucket = "Current"
        elif days_overdue <= 30:
            days_1_30 += rem
            bucket = "1–30 Days"
        elif days_overdue <= 60:
            days_31_60 += rem
            bucket = "31–60 Days"
        elif days_overdue <= 90:
            days_61_90 += rem
            bucket = "61–90 Days"
        else:
            days_90_plus += rem
            bucket = "90+ Days"

        aging_invoices.append({
            'invoice': inv,
            'remaining': rem,
            'days_overdue': max(0, days_overdue),
            'bucket': bucket
        })

    return render(request, 'finance/receivables.html', {
        'total_outstanding': total_outstanding,
        'current_amount': current_amount,
        'days_1_30': days_1_30,
        'days_31_60': days_31_60,
        'days_61_90': days_61_90,
        'days_90_plus': days_90_plus,
        'aging_invoices': aging_invoices
    })

@login_required
def payables_view(request):
    org = request.organization
    today = timezone.now().date()
    
    pending_pos = PurchaseOrder.objects.filter(organization=org).exclude(status__in=[POStatus.COMPLETED, POStatus.CANCELLED])
    total_payables = sum(po.total_amount for po in pending_pos)

    return render(request, 'finance/payables.html', {
        'total_payables': float(total_payables),
        'pending_pos': pending_pos
    })

@login_required
def profit_view(request):
    org = request.organization
    today = timezone.now().date()
    start_30 = today - timedelta(days=30)

    invoices = Invoice.objects.filter(organization=org, date__gte=start_30).exclude(status=InvoiceStatus.VOID)
    revenue = float(invoices.aggregate(total=Sum('total_amount'))['total'] or 0.00)

    pos = PurchaseOrder.objects.filter(organization=org, date__gte=start_30).exclude(status=POStatus.CANCELLED)
    cogs = float(pos.aggregate(total=Sum('total_amount'))['total'] or 0.00)

    expenses = Expense.objects.filter(organization=org, date__gte=start_30)
    total_expense = float(expenses.aggregate(total=Sum('amount'))['total'] or 0.00)

    from apps.people.models import SalaryPayment
    wages_total = float(SalaryPayment.objects.filter(organization=org, payment_date__gte=start_30).aggregate(total=Sum('amount'))['total'] or 0.00)

    gross_profit = revenue - cogs
    net_profit = gross_profit - total_expense

    gross_margin_pct = (gross_profit / revenue * 100) if revenue > 0 else 0.0
    net_margin_pct = (net_profit / revenue * 100) if revenue > 0 else 0.0

    return render(request, 'finance/profit.html', {
        'revenue': revenue,
        'cogs': cogs,
        'total_expense': total_expense,
        'wages_total': wages_total,
        'gross_profit': gross_profit,
        'net_profit': net_profit,
        'gross_margin_pct': gross_margin_pct,
        'net_margin_pct': net_margin_pct,
    })
