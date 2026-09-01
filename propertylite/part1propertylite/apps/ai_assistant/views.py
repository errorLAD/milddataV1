from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from apps.properties.models import Property, Unit
from apps.finance.models import RentInvoice, Payment, Expense
from apps.leases.models import Lease
from apps.maintenance.models import MaintenanceTicket
import datetime
import json

@login_required
def ai_chat_view(request):
    return render(request, 'ai_assistant/chat.html')

@login_required
def ai_query_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)

    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip().lower()
    except Exception:
        query = request.POST.get('query', '').strip().lower()

    if not query:
        return JsonResponse({'answer': 'Please ask a question regarding your properties, rents, or maintenance.'})

    org = request.user.organization

    # Context calculations
    invoices = RentInvoice.objects.filter(organization=org)
    total_expected = sum(inv.total_due for inv in invoices)
    total_collected = sum(inv.total_paid for inv in invoices)
    outstanding_rent = total_expected - total_collected

    today = datetime.date.today()
    in_30_days = today + datetime.timedelta(days=30)
    expiring_leases = Lease.objects.filter(organization=org, status=Lease.STATUS_ACTIVE, end_date__gte=today, end_date__lte=in_30_days)
    
    overdue_invoices = invoices.filter(status=RentInvoice.STATUS_OVERDUE)
    unpaid_tenants = [inv.tenant.get_full_name() for inv in overdue_invoices]

    props = Property.objects.filter(organization=org)

    # Intent matching
    if 'outstanding' in query or 'unpaid' in query or 'due' in query:
        answer = f"**Outstanding Rent Summary:**\n- **Total Outstanding Rent:** ${outstanding_rent:,.2f}\n- **Overdue Invoices:** {overdue_invoices.count()}\n"
        if unpaid_tenants:
            answer += f"- **Tenants with Overdue Rent:** {', '.join(set(unpaid_tenants))}"
        else:
            answer += "- All tenants are currently up to date on rent payments!"

    elif 'expire' in query or 'expiring' in query or 'lease' in query:
        answer = f"**Lease Expiry Alert:**\n- **Leases Expiring in Next 30 Days:** {expiring_leases.count()}\n"
        for l in expiring_leases:
            answer += f"\n- Unit {l.unit.unit_number} ({l.property.name}) — Tenant: **{l.tenant.get_full_name()}** (Expires: {l.end_date})"

    elif 'maintenance' in query or 'cost' in query or 'repair' in query:
        tickets = MaintenanceTicket.objects.filter(organization=org)
        highest_maint_prop = max(props, key=lambda p: sum(t.actual_total_cost for t in p.tickets.all()), default=None)
        highest_cost = sum(t.actual_total_cost for t in highest_maint_prop.tickets.all()) if highest_maint_prop else 0

        answer = f"**Maintenance & Repair Analysis:**\n- **Open Maintenance Tickets:** {tickets.exclude(status=MaintenanceTicket.STATUS_COMPLETED).count()}\n- **Property with Highest Maintenance Spend:** {highest_maint_prop.name if highest_maint_prop else 'None'} (${highest_cost:,.2f})\n"

    elif 'earn' in query or 'income' in query or 'revenue' in query:
        expenses = Expense.objects.filter(organization=org)
        tot_expenses = sum(e.amount for e in expenses)
        net_inc = total_collected - tot_expenses

        answer = f"**Financial Income Overview:**\n- **Total Collected Rent:** ${total_collected:,.2f}\n- **Total Operating Expenses:** ${tot_expenses:,.2f}\n- **Net Portfolio Profit:** ${net_inc:,.2f}"

    else:
        answer = f"**PropFlow Portfolio Summary:**\n- **Active Properties:** {props.count()}\n- **Total Units:** {sum(p.total_units_count for p in props)}\n- **Collected Rent:** ${total_collected:,.2f}\n- **Outstanding Rent:** ${outstanding_rent:,.2f}\n- Ask me anything specific like *'How much rent is outstanding?'*, *'Which leases expire this month?'*, or *'Show maintenance costs'*!"

    return JsonResponse({
        'query': query,
        'answer': answer
    })
