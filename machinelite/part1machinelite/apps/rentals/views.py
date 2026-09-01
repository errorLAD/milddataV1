import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import RentalCustomer, RentalContract
from apps.machines.models import Machine
from apps.tenants.decorators import guest_restricted

def rental_list(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    contracts = RentalContract.objects.filter(organization=tenant)
    customers = RentalCustomer.objects.filter(organization=tenant)
    machines = Machine.objects.filter(organization=tenant)

    context = {
        'contracts': contracts,
        'customers': customers,
        'machines': machines,
        'active_count': contracts.filter(status='active').count(),
    }
    return render(request, 'rentals/list.html', context)

@guest_restricted
def add_rental(request):
    if request.method == 'POST':
        tenant = request.tenant
        customer_id = request.POST.get('customer')
        machine_id = request.POST.get('machine')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        agreed_rate = float(request.POST.get('agreed_rate', 9500.00))
        deposit_amount = float(request.POST.get('deposit_amount', 20000.00))

        machine = get_object_or_404(Machine, pk=machine_id, organization=tenant)
        customer = get_object_or_404(RentalCustomer, pk=customer_id, organization=tenant)

        contract_num = f"RC-{uuid.uuid4().hex[:6].upper()}"

        RentalContract.objects.create(
            organization=tenant,
            contract_number=contract_num,
            customer=customer,
            machine=machine,
            start_date=start_date,
            end_date=end_date if end_date else None,
            agreed_rate=agreed_rate,
            deposit_amount=deposit_amount,
            handover_meter=machine.current_meter,
            status='active'
        )

        machine.status = 'rented'
        machine.save()

        messages.success(request, f"Rental contract '{contract_num}' created for {machine.name}.")
        return redirect('rental_list')
    return redirect('rental_list')
