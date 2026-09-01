from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from .models import MaintenanceLog
from apps.machines.models import Machine
from apps.tenants.models import AuditLog
from apps.tenants.decorators import guest_restricted

def maintenance_list(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    maint_logs = MaintenanceLog.objects.filter(organization=tenant)
    machines = Machine.objects.filter(organization=tenant)

    # Filters
    machine_id = request.GET.get('machine', '')
    service_type = request.GET.get('type', '')

    if machine_id:
        maint_logs = maint_logs.filter(machine_id=machine_id)
    if service_type:
        maint_logs = maint_logs.filter(service_type=service_type)

    total_cost = maint_logs.aggregate(s=Sum('cost'))['s'] or 0
    breakdown_count = MaintenanceLog.objects.filter(organization=tenant, is_breakdown=True).count()
    downtime_total = MaintenanceLog.objects.filter(organization=tenant).aggregate(s=Sum('downtime_hours'))['s'] or 0

    context = {
        'maint_logs': maint_logs,
        'machines': machines,
        'selected_machine': machine_id,
        'service_type': service_type,
        'total_cost': total_cost,
        'breakdown_count': breakdown_count,
        'downtime_total': downtime_total,
    }
    return render(request, 'maintenance/list.html', context)

@guest_restricted
def add_maintenance(request):
    if request.method == 'POST':
        tenant = request.tenant
        machine_id = request.POST.get('machine')
        machine = get_object_or_404(Machine, pk=machine_id, organization=tenant)
        
        date_str = request.POST.get('date')
        service_type = request.POST.get('service_type', 'preventive')
        cost = float(request.POST.get('cost', 0.0))
        meter_reading = float(request.POST.get('meter_reading', machine.current_meter))
        vendor = request.POST.get('vendor_mechanic', '').strip()
        parts = request.POST.get('parts_replaced', '').strip()
        description = request.POST.get('description', '').strip()
        next_meter = float(request.POST.get('next_service_meter', meter_reading + 250.0))
        is_breakdown = request.POST.get('is_breakdown') == 'on'
        downtime = float(request.POST.get('downtime_hours', 0.0))

        log = MaintenanceLog.objects.create(
            organization=tenant,
            machine=machine,
            service_type=service_type,
            date=date_str,
            meter_reading=meter_reading,
            cost=cost,
            vendor_mechanic=vendor,
            parts_replaced=parts,
            description=description,
            next_service_meter=next_meter,
            is_breakdown=is_breakdown,
            downtime_hours=downtime
        )

        if is_breakdown:
            machine.status = 'breakdown'
        else:
            machine.status = 'working'
        machine.save()

        AuditLog.objects.create(
            organization=tenant,
            user=request.user if request.user.is_authenticated else None,
            action=f"Logged maintenance ({service_type}) for {machine.name}",
            target_model="MaintenanceLog",
            details=f"Cost: ₹{cost}, Parts: {parts}"
        )

        messages.success(request, f"Maintenance record for {machine.name} logged successfully.")
        return redirect('maintenance_list')
    return redirect('maintenance_list')
