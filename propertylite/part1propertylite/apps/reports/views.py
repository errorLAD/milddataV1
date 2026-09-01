from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from apps.properties.models import Property
from apps.finance.models import RentInvoice, Expense
from apps.maintenance.models import MaintenanceTicket
from apps.leases.models import Lease
import csv

@login_required
def reports_index(request):
    org = request.user.organization
    properties = Property.objects.filter(organization=org)
    invoices = RentInvoice.objects.filter(organization=org)
    expenses = Expense.objects.filter(organization=org)
    tickets = MaintenanceTicket.objects.filter(organization=org)

    total_revenue = sum(inv.total_paid for inv in invoices)
    total_expenses = sum(exp.amount for exp in expenses)
    net_profit = total_revenue - total_expenses

    return render(request, 'reports/reports_index.html', {
        'properties': properties,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'invoices': invoices[:10],
        'expenses': expenses[:10],
        'tickets': tickets[:10],
    })

@login_required
def export_csv(request, report_type):
    org = request.user.organization
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="propflow_{report_type}_report.csv"'

    writer = csv.writer(response)

    if report_type == 'rent':
        writer.writerow(['Invoice Number', 'Tenant', 'Unit', 'Property', 'Due Date', 'Amount', 'Paid', 'Status'])
        invoices = RentInvoice.objects.filter(organization=org)
        for inv in invoices:
            writer.writerow([
                inv.invoice_number,
                inv.tenant.get_full_name(),
                inv.unit.unit_number,
                inv.property.name,
                inv.due_date,
                inv.total_due,
                inv.total_paid,
                inv.get_status_display()
            ])

    elif report_type == 'expenses':
        writer.writerow(['Date', 'Property', 'Category', 'Vendor', 'Amount', 'Description'])
        expenses = Expense.objects.filter(organization=org)
        for exp in expenses:
            writer.writerow([
                exp.date,
                exp.property.name,
                exp.get_category_display(),
                exp.vendor_name or '',
                exp.amount,
                exp.description
            ])

    elif report_type == 'properties':
        writer.writerow(['Property Name', 'Type', 'City', 'Total Units', 'Occupied Units', 'Occupancy Rate (%)', 'Current Value'])
        properties = Property.objects.filter(organization=org)
        for p in properties:
            writer.writerow([
                p.name,
                p.get_property_type_display(),
                p.city,
                p.total_units_count,
                p.occupied_units_count,
                p.occupancy_rate,
                p.current_value
            ])

    return response
