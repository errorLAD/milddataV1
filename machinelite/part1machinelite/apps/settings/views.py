from django.shortcuts import render, redirect
from django.contrib import messages
from apps.tenants.models import Organization
from apps.tenants.decorators import guest_restricted

COUNTRY_MAP = {
    'IN': {'name': 'India', 'symbol': '₹', 'code': 'INR', 'tz': 'Asia/Kolkata'},
    'US': {'name': 'United States', 'symbol': '$', 'code': 'USD', 'tz': 'America/New_York'},
    'AE': {'name': 'United Arab Emirates', 'symbol': 'AED', 'code': 'AED', 'tz': 'Asia/Dubai'},
    'UK': {'name': 'United Kingdom', 'symbol': '£', 'code': 'GBP', 'tz': 'Europe/London'},
    'DE': {'name': 'Germany / EU', 'symbol': '€', 'code': 'EUR', 'tz': 'Europe/Berlin'},
    'AU': {'name': 'Australia', 'symbol': 'A$', 'code': 'AUD', 'tz': 'Australia/Sydney'},
}

def settings_view(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    context = {
        'country_map': COUNTRY_MAP,
    }
    return render(request, 'settings/index.html', context)

@guest_restricted
def update_localization(request):
    if request.method == 'POST':
        country_code = request.POST.get('country_code', 'IN')
        tenant = request.tenant

        if country_code in COUNTRY_MAP and tenant:
            cfg = COUNTRY_MAP[country_code]
            tenant.currency_symbol = cfg['symbol']
            tenant.currency_code = cfg['code']
            tenant.timezone = cfg['tz']
            tenant.save()
            messages.success(request, f"🌍 Localization updated! Currency set to {cfg['symbol']} ({cfg['code']}).")
        return redirect('settings_index')
    return redirect('settings_index')
