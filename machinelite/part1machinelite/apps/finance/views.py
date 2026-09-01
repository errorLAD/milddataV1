from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from .models import RevenueLog, ExpenseLog
from apps.machines.models import Machine
from apps.fuel.models import FuelLog
from apps.maintenance.models import MaintenanceLog
from apps.tenants.models import AuditLog
from apps.tenants.decorators import guest_restricted

def profit_loss_view(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    machines = Machine.objects.filter(organization=tenant)

    machine_pl_list = []
    total_fleet_revenue = 0.0
    total_fleet_fuel = 0.0
    total_fleet_maintenance = 0.0
    total_fleet_other_exp = 0.0

    for m in machines:
        rev = float(RevenueLog.objects.filter(organization=tenant, machine=m).aggregate(s=Sum('amount'))['s'] or 0)
        fuel = float(FuelLog.objects.filter(organization=tenant, machine=m).aggregate(s=Sum('total_cost'))['s'] or 0)
        maint = float(MaintenanceLog.objects.filter(organization=tenant, machine=m).aggregate(s=Sum('cost'))['s'] or 0)
        other = float(ExpenseLog.objects.filter(organization=tenant, machine=m).exclude(category='fuel').exclude(category='maintenance').aggregate(s=Sum('amount'))['s'] or 0)

        total_exp = fuel + maint + other
        net_profit = rev - total_exp
        margin = (net_profit / rev * 100) if rev > 0 else 0
        roi = (net_profit / float(m.estimated_value) * 100) if m.estimated_value > 0 else 0
        cost_per_unit = (total_exp / m.current_meter) if m.current_meter > 0 else 0

        total_fleet_revenue += rev
        total_fleet_fuel += fuel
        total_fleet_maintenance += maint
        total_fleet_other_exp += other

        machine_pl_list.append({
            'machine': m,
            'revenue': rev,
            'fuel': fuel,
            'maintenance': maint,
            'other_expenses': other,
            'total_expenses': total_exp,
            'net_profit': net_profit,
            'margin': round(margin, 1),
            'roi': round(roi, 2),
            'cost_per_unit': round(cost_per_unit, 2),
        })

    machine_pl_list.sort(key=lambda x: x['net_profit'], reverse=True)
    total_fleet_expenses = total_fleet_fuel + total_fleet_maintenance + total_fleet_other_exp
    total_fleet_net_profit = total_fleet_revenue - total_fleet_expenses

    recent_revenues = RevenueLog.objects.filter(organization=tenant)[:10]
    recent_expenses = ExpenseLog.objects.filter(organization=tenant)[:10]

    context = {
        'machine_pl_list': machine_pl_list,
        'machines': machines,
        'total_fleet_revenue': total_fleet_revenue,
        'total_fleet_fuel': total_fleet_fuel,
        'total_fleet_maintenance': total_fleet_maintenance,
        'total_fleet_other_exp': total_fleet_other_exp,
        'total_fleet_expenses': total_fleet_expenses,
        'total_fleet_net_profit': total_fleet_net_profit,
        'recent_revenues': recent_revenues,
        'recent_expenses': recent_expenses,
    }
    return render(request, 'finance/profit_loss.html', context)

@guest_restricted
def add_revenue(request):
    if request.method == 'POST':
        tenant = request.tenant
        machine_id = request.POST.get('machine')
        machine = get_object_or_404(Machine, pk=machine_id, organization=tenant)
        
        date_str = request.POST.get('date')
        amount = float(request.POST.get('amount', 0.0))
        hours_billed = float(request.POST.get('hours_billed', 0.0))
        billing_type = request.POST.get('billing_type', 'hourly')
        client_name = request.POST.get('client_name', '').strip()
        status = request.POST.get('status', 'paid')
        notes = request.POST.get('notes', '').strip()

        rev = RevenueLog.objects.create(
            organization=tenant,
            machine=machine,
            date=date_str,
            amount=amount,
            hours_billed=hours_billed,
            billing_type=billing_type,
            client_name=client_name,
            status=status,
            notes=notes
        )

        AuditLog.objects.create(
            organization=tenant,
            user=request.user if request.user.is_authenticated else None,
            action=f"Added revenue invoice ₹{amount} for {machine.name}",
            target_model="RevenueLog",
            details=f"Client: {client_name}, Billed: {hours_billed} units"
        )

        messages.success(request, f"Revenue entry of ₹{amount} added for {machine.name}.")
        return redirect('profit_loss')
    return redirect('profit_loss')

@guest_restricted
def add_expense(request):
    if request.method == 'POST':
        tenant = request.tenant
        machine_id = request.POST.get('machine')
        machine = Machine.objects.filter(pk=machine_id, organization=tenant).first() if machine_id else None
        
        date_str = request.POST.get('date')
        category = request.POST.get('category', 'other')
        amount = float(request.POST.get('amount', 0.0))
        vendor = request.POST.get('vendor_recipient', '').strip()
        notes = request.POST.get('notes', '').strip()

        ExpenseLog.objects.create(
            organization=tenant,
            machine=machine,
            date=date_str,
            category=category,
            amount=amount,
            vendor_recipient=vendor,
            notes=notes
        )

        messages.success(request, f"Expense entry of ₹{amount} recorded.")
        return redirect('profit_loss')
    return redirect('profit_loss')
