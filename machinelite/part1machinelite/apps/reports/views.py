import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Sum, Avg
from datetime import date, timedelta

from apps.machines.models import Machine
from apps.fuel.models import FuelLog
from apps.maintenance.models import MaintenanceLog
from apps.finance.models import RevenueLog, ExpenseLog

def reports_overview(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    # Date range filters
    range_type = request.GET.get('range', 'month')
    today = date.today()
    if range_type == '7days':
        start_date = today - timedelta(days=7)
    elif range_type == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)

    machines = Machine.objects.filter(organization=tenant)
    fuel_logs = FuelLog.objects.filter(organization=tenant, date__gte=start_date)
    maint_logs = MaintenanceLog.objects.filter(organization=tenant, date__gte=start_date)
    rev_logs = RevenueLog.objects.filter(organization=tenant, date__gte=start_date)

    total_rev = rev_logs.aggregate(s=Sum('amount'))['s'] or 0
    total_fuel = fuel_logs.aggregate(s=Sum('total_cost'))['s'] or 0
    total_maint = maint_logs.aggregate(s=Sum('cost'))['s'] or 0
    net_profit = float(total_rev) - (float(total_fuel) + float(total_maint))

    context = {
        'range_type': range_type,
        'start_date': start_date,
        'machines': machines,
        'fuel_logs': fuel_logs[:10],
        'maint_logs': maint_logs[:10],
        'rev_logs': rev_logs[:10],
        'total_rev': total_rev,
        'total_fuel': total_fuel,
        'total_maint': total_maint,
        'net_profit': net_profit,
    }
    return render(request, 'reports/overview.html', context)

def export_fleet_csv(request):
    tenant = request.tenant
    if not tenant:
        return HttpResponse("Unauthorized", status=401)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="MachineOS_Fleet_Report_{date.today()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Machine Name', 'Reg Number', 'Category', 'Make & Model', 'Tracking Mode', 'Current Meter', 'Daily Rate', 'Status'])

    machines = Machine.objects.filter(organization=tenant)
    for m in machines:
        writer.writerow([
            m.name, m.reg_number, m.get_category_display(), m.make_model,
            m.get_tracking_type_display(), m.current_meter, m.daily_rate, m.get_status_display()
        ])

    return response
