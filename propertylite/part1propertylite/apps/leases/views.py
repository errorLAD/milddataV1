from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Lease
from apps.properties.models import Property, Unit
from apps.core.models import User, AuditLog, Notification
from apps.core.utils.security import guest_restricted
import datetime

@login_required
def lease_list(request):
    org = request.user.organization
    leases = Lease.objects.filter(organization=org)
    
    status_filter = request.GET.get('status')
    if status_filter:
        leases = leases.filter(status=status_filter)
        
    return render(request, 'leases/lease_list.html', {
        'leases': leases,
        'status_choices': Lease.STATUS_CHOICES
    })

@login_required
def lease_detail(request, pk):
    org = request.user.organization
    lease = get_object_or_404(Lease, id=pk, organization=org)
    invoices = lease.invoices.all()
    return render(request, 'leases/lease_detail.html', {'lease': lease, 'invoices': invoices})

@login_required
@guest_restricted
def lease_create(request):
    org = request.user.organization
    properties = Property.objects.filter(organization=org)
    vacant_units = Unit.objects.filter(property__organization=org, status=Unit.STATUS_VACANT)
    all_units = Unit.objects.filter(property__organization=org)
    tenants = User.objects.filter(organization=org, role=User.ROLE_TENANT)

    if request.method == 'POST':
        unit_id = request.POST.get('unit')
        tenant_id = request.POST.get('tenant')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        monthly_rent = request.POST.get('monthly_rent')
        security_deposit = request.POST.get('security_deposit')

        unit = get_object_or_404(Unit, id=unit_id, property__organization=org)
        tenant = get_object_or_404(User, id=tenant_id, organization=org)

        lease = Lease.objects.create(
            organization=org,
            property=unit.property,
            unit=unit,
            tenant=tenant,
            start_date=start_date,
            end_date=end_date,
            monthly_rent=monthly_rent,
            security_deposit=security_deposit,
            status=Lease.STATUS_ACTIVE
        )

        # Update unit status to OCCUPIED
        unit.status = Unit.STATUS_OCCUPIED
        unit.save()

        # Create notification
        Notification.objects.create(
            organization=org,
            recipient=tenant,
            title="New Lease Agreement Created",
            message=f"Your lease for Unit {unit.unit_number} ({unit.property.name}) is now Active.",
            notification_type=Notification.TYPE_LEASE
        )

        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action=f"Created Lease #{lease.id} for Unit {unit.unit_number}",
            entity_type="Lease",
            entity_id=str(lease.id)
        )

        messages.success(request, f"Lease #{lease.id} created successfully!")
        return redirect('lease_detail', pk=lease.id)

    return render(request, 'leases/lease_form.html', {
        'properties': properties,
        'units': vacant_units or all_units,
        'tenants': tenants,
    })
