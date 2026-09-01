from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Property, Building, Unit
from apps.core.models import AuditLog, User
from apps.core.utils.security import guest_restricted

@login_required
def property_list(request):
    org = request.user.organization
    properties = Property.objects.filter(organization=org)
    
    # Filtering
    p_type = request.GET.get('type')
    if p_type:
        properties = properties.filter(property_type=p_type)
        
    return render(request, 'properties/property_list.html', {
        'properties': properties,
        'property_types': Property.TYPE_CHOICES
    })

@login_required
def property_detail(request, pk):
    org = request.user.organization
    prop = get_object_or_404(Property, id=pk, organization=org)
    units = prop.units.all()
    leases = prop.leases.all()
    tickets = prop.tickets.all()
    expenses = prop.expenses.all()
    
    return render(request, 'properties/property_detail.html', {
        'property': prop,
        'units': units,
        'leases': leases,
        'tickets': tickets,
        'expenses': expenses,
    })

@login_required
@guest_restricted
def property_create(request):
    org = request.user.organization
    owners = User.objects.filter(organization=org, role=User.ROLE_PROPERTY_OWNER)
    managers = User.objects.filter(organization=org, role=User.ROLE_PROPERTY_MANAGER)

    if request.method == 'POST':
        name = request.POST.get('name')
        p_type = request.POST.get('property_type')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        purchase_value = request.POST.get('purchase_value') or 0
        current_value = request.POST.get('current_value') or 0
        owner_id = request.POST.get('owner')
        notes = request.POST.get('notes')

        owner = User.objects.filter(id=owner_id, organization=org).first() if owner_id else None

        new_prop = Property.objects.create(
            organization=org,
            name=name,
            property_type=p_type,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            purchase_value=purchase_value,
            current_value=current_value,
            owner=owner,
            notes=notes
        )

        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action=f"Created Property {new_prop.name}",
            entity_type="Property",
            entity_id=str(new_prop.id)
        )

        messages.success(request, f"Property '{new_prop.name}' created successfully!")
        return redirect('property_detail', pk=new_prop.id)

    return render(request, 'properties/property_form.html', {
        'owners': owners,
        'managers': managers,
        'property_types': Property.TYPE_CHOICES
    })

@login_required
@guest_restricted
def unit_create(request, property_pk):
    org = request.user.organization
    prop = get_object_or_404(Property, id=property_pk, organization=org)

    if request.method == 'POST':
        unit_number = request.POST.get('unit_number')
        floor = request.POST.get('floor') or 1
        u_type = request.POST.get('type')
        area = request.POST.get('area_sqft') or 850
        bedrooms = request.POST.get('bedrooms') or 2
        bathrooms = request.POST.get('bathrooms') or 2.0
        rent = request.POST.get('monthly_rent') or 1500
        deposit = request.POST.get('security_deposit') or 1500

        unit = Unit.objects.create(
            property=prop,
            unit_number=unit_number,
            floor=floor,
            type=u_type,
            area_sqft=area,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            monthly_rent=rent,
            security_deposit=deposit
        )

        messages.success(request, f"Unit '{unit.unit_number}' added to {prop.name}!")
        return redirect('property_detail', pk=prop.id)

    return render(request, 'properties/unit_form.html', {
        'property': prop,
        'unit_types': Unit.UNIT_TYPE_CHOICES
    })
