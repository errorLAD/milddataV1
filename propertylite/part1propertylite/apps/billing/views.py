from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.models import Organization, User, AuditLog
from apps.core.utils.security import guest_restricted

CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'INR': '₹',
    'CAD': 'C$',
    'AUD': 'A$',
    'AED': 'AED ',
    'SAR': 'SAR ',
    'JPY': '¥',
    'SGD': 'S$',
}

@login_required
def billing_index(request):
    org = request.user.organization
    users = User.objects.filter(organization=org)

    if request.method == 'POST':
        if request.user.is_guest:
            messages.warning(request, "🔒 Guest Access Mode: Updating organization settings requires a full property manager account.")
            return redirect('guest_upgrade')

        plan = request.POST.get('plan')
        currency_code = request.POST.get('currency_code')

        if plan in [Organization.PLAN_STARTER, Organization.PLAN_PROFESSIONAL, Organization.PLAN_BUSINESS]:
            org.plan = plan

        if currency_code in CURRENCY_SYMBOLS:
            org.currency_code = currency_code
            org.currency_symbol = CURRENCY_SYMBOLS[currency_code]

        org.save()

        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action=f"Updated Organization Settings (Plan: {org.get_plan_display()}, Currency: {org.currency_code})",
            entity_type="Organization",
            entity_id=str(org.id)
        )

        messages.success(request, f"Organization settings updated! Currency set to {org.currency_code} ({org.currency_symbol}).")
        return redirect('billing')

    return render(request, 'billing/billing_index.html', {
        'org': org,
        'users': users,
        'plans': Organization.PLAN_CHOICES,
        'currencies': Organization.CURRENCY_CHOICES
    })
