from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Avg
from .models import FuelLog
from apps.machines.models import Machine
from apps.tenants.models import AuditLog
from apps.tenants.decorators import guest_restricted

def fuel_list(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    fuel_logs = FuelLog.objects.filter(organization=tenant)
    machines = Machine.objects.filter(organization=tenant)

    # Filters
    machine_id = request.GET.get('machine', '')
    flag_only = request.GET.get('abnormal', '')

    if machine_id:
        fuel_logs = fuel_logs.filter(machine_id=machine_id)
    if flag_only == '1':
        fuel_logs = fuel_logs.filter(is_abnormal_flag=True)

    total_liters = fuel_logs.aggregate(s=Sum('fuel_liters'))['s'] or 0
    total_cost = fuel_logs.aggregate(s=Sum('total_cost'))['s'] or 0
    avg_efficiency = fuel_logs.aggregate(a=Avg('efficiency_rate'))['a'] or 0
    abnormal_count = FuelLog.objects.filter(organization=tenant, is_abnormal_flag=True).count()

    context = {
        'fuel_logs': fuel_logs,
        'machines': machines,
        'selected_machine': machine_id,
        'flag_only': flag_only,
        'total_liters': total_liters,
        'total_cost': total_cost,
        'avg_efficiency': round(avg_efficiency, 2),
        'abnormal_count': abnormal_count,
    }
    return render(request, 'fuel/list.html', context)

@guest_restricted
def add_fuel(request):
    if request.method == 'POST':
        tenant = request.tenant
        machine_id = request.POST.get('machine')
        machine = get_object_or_404(Machine, pk=machine_id, organization=tenant)
        
        date_str = request.POST.get('date')
        liters = float(request.POST.get('fuel_liters', 0.0))
        cost_per_l = float(request.POST.get('cost_per_liter', 94.50))
        meter_reading = float(request.POST.get('meter_reading', machine.current_meter))
        hours_run = float(request.POST.get('hours_run_since_last', 0.0))
        vendor = request.POST.get('fuel_vendor', '').strip()
        notes = request.POST.get('notes', '').strip()

        log = FuelLog.objects.create(
            organization=tenant,
            machine=machine,
            date=date_str,
            fuel_liters=liters,
            cost_per_liter=cost_per_l,
            meter_reading=meter_reading,
            hours_run_since_last=hours_run,
            fuel_vendor=vendor,
            notes=notes
        )

        AuditLog.objects.create(
            organization=tenant,
            user=request.user if request.user.is_authenticated else None,
            action=f"Logged {liters}L fuel for {machine.name}",
            target_model="FuelLog",
            details=f"Cost: ₹{log.total_cost}, Abnormal: {log.is_abnormal_flag}"
        )

        if log.is_abnormal_flag:
            messages.warning(request, f"Fuel logged! ⚠️ High consumption flag triggered ({log.efficiency_rate} L/Hr).")
        else:
            messages.success(request, f"Refuel entry of {liters}L logged for {machine.name}.")
        return redirect('fuel_list')
    return redirect('fuel_list')
