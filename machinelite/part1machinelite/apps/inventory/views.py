from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import SparePart, PartTransaction
from apps.machines.models import Machine
from apps.tenants.decorators import guest_restricted

def inventory_list(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    parts = SparePart.objects.filter(organization=tenant)
    machines = Machine.objects.filter(organization=tenant)
    low_stock_parts = [p for p in parts if p.is_low_stock]

    context = {
        'parts': parts,
        'machines': machines,
        'low_stock_parts': low_stock_parts,
        'low_stock_count': len(low_stock_parts),
    }
    return render(request, 'inventory/list.html', context)

@guest_restricted
def add_spare_part(request):
    if request.method == 'POST':
        tenant = request.tenant
        name = request.POST.get('name')
        sku = request.POST.get('sku')
        category = request.POST.get('category', 'General')
        stock_quantity = int(request.POST.get('stock_quantity', 10))
        min_threshold = int(request.POST.get('min_stock_threshold', 3))
        unit_cost = float(request.POST.get('unit_cost', 1500.00))
        supplier = request.POST.get('supplier_name', '')

        SparePart.objects.create(
            organization=tenant,
            name=name,
            sku=sku,
            category=category,
            stock_quantity=stock_quantity,
            min_stock_threshold=min_threshold,
            unit_cost=unit_cost,
            supplier_name=supplier
        )

        messages.success(request, f"Spare Part '{name}' added to inventory.")
        return redirect('inventory_list')
    return redirect('inventory_list')

@guest_restricted
def stock_transaction(request):
    if request.method == 'POST':
        tenant = request.tenant
        part_id = request.POST.get('spare_part')
        trans_type = request.POST.get('transaction_type', 'stock_out')
        quantity = int(request.POST.get('quantity', 1))
        machine_id = request.POST.get('machine')
        notes = request.POST.get('notes', '')

        part = get_object_or_404(SparePart, pk=part_id, organization=tenant)
        machine = Machine.objects.filter(pk=machine_id, organization=tenant).first() if machine_id else None

        if trans_type == 'stock_out':
            if part.stock_quantity < quantity:
                messages.error(request, f"Insufficient stock for {part.name}. Only {part.stock_quantity} available.")
                return redirect('inventory_list')
            part.stock_quantity -= quantity
        else:
            part.stock_quantity += quantity

        part.save()

        PartTransaction.objects.create(
            organization=tenant,
            spare_part=part,
            machine=machine,
            transaction_type=trans_type,
            quantity=quantity,
            notes=notes
        )

        messages.success(request, f"Stock transaction recorded for {part.name}.")
        return redirect('inventory_list')
    return redirect('inventory_list')
