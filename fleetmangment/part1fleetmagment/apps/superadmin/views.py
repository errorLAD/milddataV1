from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from apps.fleet.models import Organization, Subscription, Vehicle, User

@login_required
def superadmin_dashboard(request):
    if not request.user.is_superuser and request.user.role != 'OWNER':
        return redirect('dashboard')
        
    organizations = Organization.objects.all()
    subscriptions = Subscription.objects.all()
    
    total_tenants = organizations.count()
    active_subs = subscriptions.filter(status='ACTIVE').count()
    mrr = subscriptions.filter(status='ACTIVE').aggregate(s=Sum('monthly_price'))['s'] or 0.0
    total_vehicles_all = Vehicle.objects.count()
    total_users_all = User.objects.count()

    context = {
        'total_tenants': total_tenants,
        'active_subs': active_subs,
        'mrr': mrr,
        'total_vehicles_all': total_vehicles_all,
        'total_users_all': total_users_all,
        'organizations': organizations,
        'subscriptions': subscriptions,
    }
    return render(request, 'superadmin/dashboard.html', context)
