import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Trip
from apps.machines.models import Machine
from apps.operators.models import Operator
from apps.projects.models import Project
from apps.tenants.decorators import guest_restricted

def trip_list(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    trips = Trip.objects.filter(organization=tenant)
    machines = Machine.objects.filter(organization=tenant)
    operators = Operator.objects.filter(organization=tenant)
    projects = Project.objects.filter(organization=tenant)

    context = {
        'trips': trips,
        'machines': machines,
        'operators': operators,
        'projects': projects,
    }
    return render(request, 'trips/list.html', context)

@guest_restricted
def add_trip(request):
    if request.method == 'POST':
        tenant = request.tenant
        machine_id = request.POST.get('machine')
        driver_id = request.POST.get('driver')
        project_id = request.POST.get('project')
        pickup = request.POST.get('pickup_location')
        drop = request.POST.get('drop_location')
        distance = float(request.POST.get('distance_km', 0.0))
        expenses = float(request.POST.get('expenses', 0.0))

        machine = get_object_or_404(Machine, pk=machine_id, organization=tenant)
        driver = get_object_or_404(Operator, pk=driver_id, organization=tenant)
        project = Project.objects.filter(pk=project_id, organization=tenant).first() if project_id else None

        trip_num = f"TRIP-{uuid.uuid4().hex[:6].upper()}"

        Trip.objects.create(
            organization=tenant,
            trip_number=trip_num,
            machine=machine,
            driver=driver,
            project=project,
            pickup_location=pickup,
            drop_location=drop,
            distance_km=distance,
            expenses=expenses,
            status='in_progress'
        )

        messages.success(request, f"Trip '{trip_num}' dispatched successfully.")
        return redirect('trip_list')
    return redirect('trip_list')
