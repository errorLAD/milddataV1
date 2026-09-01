from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.models import User, AuditLog
from apps.core.utils.security import guest_restricted
from .models import TenantProfile
from apps.leases.models import Lease
from apps.finance.models import RentInvoice, Payment
from apps.maintenance.models import MaintenanceTicket

@login_required
def tenant_list(request):
    org = request.user.organization
    tenants = User.objects.filter(organization=org, role=User.ROLE_TENANT)
    return render(request, 'tenants/tenant_list.html', {'tenants': tenants})

@login_required
def tenant_detail(request, pk):
    org = request.user.organization
    tenant_user = get_object_or_404(User, id=pk, organization=org, role=User.ROLE_TENANT)
    profile = getattr(tenant_user, 'tenant_profile', None)
    
    leases = Lease.objects.filter(tenant=tenant_user)
    active_lease = leases.filter(status=Lease.STATUS_ACTIVE).first()
    invoices = RentInvoice.objects.filter(tenant=tenant_user)
    payments = Payment.objects.filter(tenant=tenant_user)
    tickets = MaintenanceTicket.objects.filter(tenant=tenant_user)

    return render(request, 'tenants/tenant_detail.html', {
        'tenant_user': tenant_user,
        'profile': profile,
        'leases': leases,
        'active_lease': active_lease,
        'invoices': invoices,
        'payments': payments,
        'tickets': tickets,
    })

@login_required
@guest_restricted
def tenant_create(request):
    org = request.user.organization
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        emergency_name = request.POST.get('emergency_name')
        emergency_phone = request.POST.get('emergency_phone')

        username = email.split('@')[0] if email else f"tenant_{User.objects.count()+1}"
        
        tenant_user = User.objects.create_user(
            username=username,
            email=email,
            password="PropFlowTenant123!",
            first_name=first_name,
            last_name=last_name,
            organization=org,
            role=User.ROLE_TENANT,
            phone=phone
        )

        TenantProfile.objects.create(
            organization=org,
            user=tenant_user,
            emergency_contact_name=emergency_name,
            emergency_contact_phone=emergency_phone,
            kyc_status=TenantProfile.KYC_VERIFIED
        )

        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action=f"Created Tenant {tenant_user.get_full_name()}",
            entity_type="Tenant",
            entity_id=str(tenant_user.id)
        )

        messages.success(request, f"Tenant '{tenant_user.get_full_name()}' created successfully!")
        return redirect('tenant_detail', pk=tenant_user.id)

    return render(request, 'tenants/tenant_form.html')
