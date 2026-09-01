from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
from .models import Machine, MeterLog, MachineLocation, GeofenceZone, LocationPing
from .health import HealthScoreCalculator
from apps.fuel.models import FuelLog
from apps.maintenance.models import MaintenanceLog
from apps.finance.models import RevenueLog, ExpenseLog
from apps.documents.models import MachineDocument
from apps.operators.models import Operator
from apps.tenants.models import AuditLog
from apps.tenants.decorators import guest_restricted

def machine_list(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    machines = Machine.objects.filter(organization=tenant)

    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('q', '')

    if status_filter:
        machines = machines.filter(status=status_filter)
    if category_filter:
        machines = machines.filter(category=category_filter)
    if search_query:
        machines = machines.filter(Q(name__icontains=search_query) | Q(reg_number__icontains=search_query) | Q(make_model__icontains=search_query))

    machine_health_list = []
    for m in machines:
        calc = HealthScoreCalculator(m, tenant)
        health = calc.calculate()
        loc = getattr(m, 'location', None)
        machine_health_list.append({
            'machine': m,
            'health': health,
            'location': loc,
        })

    total_count = machines.count()
    working_count = Machine.objects.filter(organization=tenant, status='working').count()
    idle_count = Machine.objects.filter(organization=tenant, status='idle').count()
    maintenance_count = Machine.objects.filter(organization=tenant, status='maintenance').count()
    breakdown_count = Machine.objects.filter(organization=tenant, status='breakdown').count()

    context = {
        'machine_health_list': machine_health_list,
        'machines': machines,
        'total_count': total_count,
        'working_count': working_count,
        'idle_count': idle_count,
        'maintenance_count': maintenance_count,
        'breakdown_count': breakdown_count,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'search_query': search_query,
    }
    return render(request, 'machines/list.html', context)

def machine_detail(request, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    machine = get_object_or_404(Machine, pk=pk, organization=tenant)

    calc = HealthScoreCalculator(machine, tenant)
    health = calc.calculate()
    location = getattr(machine, 'location', None)
    operator = Operator.objects.filter(organization=tenant, assigned_machine=machine).first()

    meter_logs = MeterLog.objects.filter(organization=tenant, machine=machine)[:10]
    fuel_logs = FuelLog.objects.filter(organization=tenant, machine=machine)[:10]
    maint_logs = MaintenanceLog.objects.filter(organization=tenant, machine=machine)[:10]
    documents = MachineDocument.objects.filter(organization=tenant, machine=machine)

    rev_total = RevenueLog.objects.filter(organization=tenant, machine=machine).aggregate(s=Sum('amount'))['s'] or 0
    fuel_total = FuelLog.objects.filter(organization=tenant, machine=machine).aggregate(s=Sum('total_cost'))['s'] or 0
    maint_total = MaintenanceLog.objects.filter(organization=tenant, machine=machine).aggregate(s=Sum('cost'))['s'] or 0
    total_exp = float(fuel_total) + float(maint_total)
    net_profit = float(rev_total) - total_exp

    context = {
        'machine': machine,
        'health': health,
        'location': location,
        'operator': operator,
        'meter_logs': meter_logs,
        'fuel_logs': fuel_logs,
        'maint_logs': maint_logs,
        'documents': documents,
        'rev_total': rev_total,
        'fuel_total': fuel_total,
        'maint_total': maint_total,
        'total_exp': total_exp,
        'net_profit': net_profit,
    }
    return render(request, 'machines/detail.html', context)

def fleet_map_view(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    machines = Machine.objects.filter(organization=tenant)

    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')

    if status_filter:
        machines = machines.filter(status=status_filter)
    if category_filter:
        machines = machines.filter(category=category_filter)

    map_locations = []
    for m in machines:
        loc = getattr(m, 'location', None)
        op = Operator.objects.filter(organization=tenant, assigned_machine=m).first()
        if loc:
            map_locations.append({
                'id': m.pk,
                'name': m.name,
                'reg_number': m.reg_number,
                'category': m.get_category_display(),
                'status': m.status,
                'status_label': m.get_status_display(),
                'lat': loc.latitude,
                'lng': loc.longitude,
                'location_name': loc.location_name,
                'speed': loc.speed_kmh,
                'ignition': loc.ignition_on,
                'operator_name': op.name if op else 'Unassigned',
                'meter': f"{m.current_meter:.1f} {m.unit_label}",
                'last_ping': loc.last_ping_time.strftime("%d %b %Y %H:%M"),
            })

    geofences = GeofenceZone.objects.filter(organization=tenant)

    context = {
        'map_locations': map_locations,
        'machines': machines,
        'geofences': geofences,
        'status_filter': status_filter,
        'category_filter': category_filter,
    }
    return render(request, 'machines/map.html', context)

def health_matrix_view(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    machines = Machine.objects.filter(organization=tenant)
    matrix = []

    excellent_count = 0
    good_count = 0
    warning_count = 0
    critical_count = 0

    for m in machines:
        calc = HealthScoreCalculator(m, tenant)
        h = calc.calculate()
        if h['status'] == 'excellent':
            excellent_count += 1
        elif h['status'] == 'good':
            good_count += 1
        elif h['status'] == 'warning':
            warning_count += 1
        else:
            critical_count += 1

        matrix.append({
            'machine': m,
            'health': h,
        })

    matrix.sort(key=lambda x: x['health']['score'])

    context = {
        'matrix': matrix,
        'total_count': len(matrix),
        'excellent_count': excellent_count,
        'good_count': good_count,
        'warning_count': warning_count,
        'critical_count': critical_count,
    }
    return render(request, 'machines/health_matrix.html', context)

@guest_restricted
def add_machine(request):
    if request.method == 'POST':
        tenant = request.tenant
        name = request.POST.get('name', '').strip()
        reg_number = request.POST.get('reg_number', '').strip()
        category = request.POST.get('category', 'jcb')
        make_model = request.POST.get('make_model', '').strip()
        tracking_type = request.POST.get('tracking_type', 'hours')
        current_meter = float(request.POST.get('current_meter', 0.0))
        status = request.POST.get('status', 'working')
        daily_rate = float(request.POST.get('daily_rate', 9500.00))

        if not name or not reg_number:
            messages.error(request, "Machine Name and Registration Number are required.")
            return redirect('machine_list')

        machine = Machine.objects.create(
            organization=tenant,
            name=name,
            reg_number=reg_number,
            category=category,
            make_model=make_model,
            tracking_type=tracking_type,
            current_meter=current_meter,
            status=status,
            daily_rate=daily_rate
        )

        MachineLocation.objects.create(
            machine=machine,
            latitude=12.9716,
            longitude=77.5946,
            location_name="Central Logistics Yard",
            speed_kmh=0.0,
            ignition_on=False
        )

        AuditLog.objects.create(
            organization=tenant,
            user=request.user if request.user.is_authenticated else None,
            action=f"Added machine {machine.name}",
            target_model="Machine",
            details=f"Reg: {reg_number}, Category: {category}"
        )
        messages.success(request, f"Machine '{machine.name}' added successfully!")
        return redirect('machine_list')
    return redirect('machine_list')

@guest_restricted
def update_location(request, pk):
    """
    Manually update GPS location, coordinates, speed, and ignition status for a machine.
    """
    if request.method == 'POST':
        tenant = request.tenant
        machine = get_object_or_404(Machine, pk=pk, organization=tenant)
        
        location_name = request.POST.get('location_name', '').strip()
        latitude = float(request.POST.get('latitude', 12.9716))
        longitude = float(request.POST.get('longitude', 77.5946))
        speed_kmh = float(request.POST.get('speed_kmh', 0.0))
        ignition_on = request.POST.get('ignition_on') == 'true'

        loc, _ = MachineLocation.objects.get_or_create(machine=machine)
        loc.location_name = location_name if location_name else loc.location_name
        loc.latitude = latitude
        loc.longitude = longitude
        loc.speed_kmh = speed_kmh
        loc.ignition_on = ignition_on
        loc.save()

        LocationPing.objects.create(
            machine=machine,
            latitude=latitude,
            longitude=longitude,
            location_name=loc.location_name,
            speed_kmh=speed_kmh
        )

        AuditLog.objects.create(
            organization=tenant,
            user=request.user if request.user.is_authenticated else None,
            action=f"Updated GPS Location for {machine.name}",
            target_model="MachineLocation",
            details=f"Address: {loc.location_name}, GPS: ({latitude}, {longitude})"
        )

        messages.success(request, f"📍 GPS Location for '{machine.name}' updated to '{loc.location_name}'!")
        return redirect('machine_detail', pk=machine.pk)
    return redirect('machine_detail', pk=pk)

@guest_restricted
def log_meter(request, pk):
    if request.method == 'POST':
        tenant = request.tenant
        machine = get_object_or_404(Machine, pk=pk, organization=tenant)
        new_reading = float(request.POST.get('meter_reading', 0.0))
        date_str = request.POST.get('date')
        notes = request.POST.get('notes', '')

        hours_worked = max(0.0, new_reading - machine.current_meter)
        machine.current_meter = new_reading
        machine.save()

        MeterLog.objects.create(
            organization=tenant,
            machine=machine,
            date=date_str,
            meter_reading=new_reading,
            hours_worked=hours_worked,
            recorded_by=request.user if request.user.is_authenticated else None,
            notes=notes
        )
        messages.success(request, f"Logged {hours_worked} {machine.unit_label} for {machine.name}.")
        return redirect('machine_detail', pk=machine.pk)
    return redirect('machine_list')
