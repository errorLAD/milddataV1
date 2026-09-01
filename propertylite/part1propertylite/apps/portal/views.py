from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.leases.models import Lease
from apps.finance.models import RentInvoice, Payment, Expense
from apps.maintenance.models import MaintenanceTicket
from apps.properties.models import Property
from apps.core.models import Notification

@login_required
def tenant_pwa(request):
    user = request.user
    org = user.organization

    lease = Lease.objects.filter(tenant=user, status=Lease.STATUS_ACTIVE).first()
    unit = lease.unit if lease else None
    prop = lease.property if lease else None

    # Invoices & Tickets
    invoices = RentInvoice.objects.filter(tenant=user)
    pending_invoice = invoices.filter(status__in=[RentInvoice.STATUS_PENDING, RentInvoice.STATUS_OVERDUE]).first()
    tickets = MaintenanceTicket.objects.filter(tenant=user)
    active_tickets = tickets.exclude(status=MaintenanceTicket.STATUS_COMPLETED)
    announcements = Notification.objects.filter(recipient=user)[:3]

    return render(request, 'portal/tenant_pwa.html', {
        'lease': lease,
        'unit': unit,
        'property': prop,
        'pending_invoice': pending_invoice,
        'invoices': invoices,
        'tickets': tickets,
        'active_tickets': active_tickets,
        'announcements': announcements,
    })

@login_required
def owner_dashboard(request):
    user = request.user
    org = user.organization

    # If role is Property Owner, filter properties owned by this user, else show all org properties
    if user.role == user.ROLE_PROPERTY_OWNER:
        properties = Property.objects.filter(organization=org, owner=user)
    else:
        properties = Property.objects.filter(organization=org)

    total_portfolio_value = sum(p.current_value for p in properties)
    total_units = sum(p.total_units_count for p in properties)
    occupied_units = sum(p.occupied_units_count for p in properties)
    overall_occupancy = round((occupied_units / total_units * 100), 1) if total_units > 0 else 0

    # Rent & Expenses for these properties
    invoices = RentInvoice.objects.filter(unit__property__in=properties)
    expenses = Expense.objects.filter(property__in=properties)

    total_income = sum(inv.total_paid for inv in invoices)
    total_expenses = sum(exp.amount for exp in expenses)
    net_income = total_income - total_expenses
    roi_pct = round((float(net_income * 12) / float(total_portfolio_value) * 100), 2) if total_portfolio_value > 0 else 0.0

    return render(request, 'portal/owner_dashboard.html', {
        'properties': properties,
        'total_portfolio_value': total_portfolio_value,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'overall_occupancy': overall_occupancy,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'roi_pct': roi_pct,
    })
