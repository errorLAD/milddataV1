from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from apps.tenants.models import Organization, AuditLog
from apps.machines.models import Machine
from apps.billing.models import Subscription

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def admin_portal_dashboard(request):
    """
    System Admin Portal Dashboard - Strictly restricted to superusers.
    """
    organizations = Organization.objects.all()
    total_machines = Machine.objects.count()
    total_subscriptions = Subscription.objects.count()
    audit_logs = AuditLog.objects.all()[:20]

    context = {
        'organizations': organizations,
        'total_machines': total_machines,
        'total_subscriptions': total_subscriptions,
        'audit_logs': audit_logs,
    }
    return render(request, 'admin_portal/index.html', context)
