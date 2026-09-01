from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Subscription
from apps.machines.models import Machine
from apps.tenants.decorators import guest_restricted

def billing_plans_view(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    sub = Subscription.objects.filter(organization=tenant).first()
    current_count = Machine.objects.filter(organization=tenant).count()

    context = {
        'subscription': sub,
        'current_count': current_count,
        'machine_limit': sub.machine_limit if sub else 25,
    }
    return render(request, 'billing/plans.html', context)

@guest_restricted
def upgrade_plan(request):
    if request.method == 'POST':
        tier = request.POST.get('tier', 'pro')
        tenant = request.tenant

        sub, _ = Subscription.objects.get_or_create(organization=tenant)
        if tier == 'starter':
            sub.plan_tier = 'starter'
            sub.machine_limit = 5
            sub.monthly_price = 1999.00
        elif tier == 'enterprise':
            sub.plan_tier = 'enterprise'
            sub.machine_limit = 999
            sub.monthly_price = 14999.00
        else:
            sub.plan_tier = 'pro'
            sub.machine_limit = 25
            sub.monthly_price = 4999.00
        sub.save()

        messages.success(request, f"🎉 Successfully updated plan to {sub.get_plan_tier_display()}!")
        return redirect('billing_plans')
    return redirect('billing_plans')
