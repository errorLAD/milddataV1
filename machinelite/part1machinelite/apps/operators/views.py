from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Operator, OperatorAttendance, OperatorIncident
from apps.machines.models import Machine
from apps.tenants.decorators import guest_restricted

def operator_list(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    operators = Operator.objects.filter(organization=tenant)
    machines = Machine.objects.filter(organization=tenant)

    context = {
        'operators': operators,
        'machines': machines,
        'active_count': operators.filter(status='active').count(),
    }
    return render(request, 'operators/list.html', context)

@guest_restricted
def add_operator(request):
    if request.method == 'POST':
        tenant = request.tenant
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        license_number = request.POST.get('license_number')
        license_expiry = request.POST.get('license_expiry')
        machine_id = request.POST.get('assigned_machine')
        daily_salary = float(request.POST.get('daily_salary', 800.00))

        machine = Machine.objects.filter(pk=machine_id, organization=tenant).first() if machine_id else None

        Operator.objects.create(
            organization=tenant,
            name=name,
            phone=phone,
            license_number=license_number,
            license_expiry=license_expiry if license_expiry else None,
            assigned_machine=machine,
            daily_salary=daily_salary
        )

        messages.success(request, f"Operator / Driver '{name}' added successfully.")
        return redirect('operator_list')
    return redirect('operator_list')
