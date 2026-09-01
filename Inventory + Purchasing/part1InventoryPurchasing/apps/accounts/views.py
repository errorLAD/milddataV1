from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
import time
import uuid

from apps.accounts.models import Organization, UserProfile
from apps.accounts.decorators import require_full_account
from apps.core.models import AuditLog, Notification
from apps.inventory.models import Product, ProductCategory, ProductUnit, Warehouse, Inventory

def login_view(request):
    if request.user.is_authenticated and not request.session.get('is_guest', False):
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Invalidate any guest mode flags on actual login
            request.session.pop('is_guest', None)
            request.session.pop('guest_expiry', None)

            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})

def guest_login_view(request):
    """
    Creates a temporary guest session with an isolated demo organization
    and auto-expiring 2-hour duration.
    """
    unique_id = uuid.uuid4().hex[:8]
    guest_username = f"guest_{unique_id}"

    with transaction.atomic():
        guest_user = User.objects.create_user(
            username=guest_username,
            email=f"{guest_username}@demo.stockflow.app",
            password=f"GuestPass_{unique_id}"
        )

        # Isolated Guest Demo Organization
        org, _ = Organization.objects.get_or_create(
            name='StockFlow Demo Co. (Guest Mode)',
            defaults={
                'country': 'United States',
                'currency_code': 'USD',
                'currency_symbol': '$',
                'currency_position': 'prefix',
                'tax_name': 'Sales Tax',
                'tax_rate': Decimal('8.50'),
                'address': '100 Demo Plaza, San Francisco, CA'
            }
        )

        # Seed minimal demo data for guest if new org
        wh, _ = Warehouse.objects.get_or_create(organization=org, code='WH-DEMO', defaults={'name': 'Demo Warehouse', 'is_primary': True})
        unit_pcs, _ = ProductUnit.objects.get_or_create(organization=org, name='Piece', abbreviation='pcs')
        p1, _ = Product.objects.get_or_create(organization=org, sku='DEMO-100', defaults={
            'name': 'Wireless Demo Router',
            'purchase_price': Decimal('50.00'),
            'selling_price': Decimal('95.00'),
            'unit': unit_pcs,
            'reorder_level': 5
        })
        Inventory.objects.get_or_create(organization=org, product=p1, warehouse=wh, defaults={'quantity': 25})

        UserProfile.objects.create(
            user=guest_user,
            organization=org,
            role='VIEWER'
        )

    # Log in guest user & set session flags
    login(request, guest_user)
    request.session['is_guest'] = True
    request.session['guest_expiry'] = time.time() + 7200 # 2 Hours expiration

    AuditLog.objects.create(
        organization=org,
        user=guest_user,
        action='Guest Session Started',
        object_type='GuestSession',
        object_repr=guest_username
    )

    messages.info(request, "⚡ You are browsing in Guest Mode. Explore demo features or create an account anytime.")
    return redirect('dashboard')

def register_view(request):
    if request.user.is_authenticated and not request.session.get('is_guest', False):
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        company_name = request.POST.get('company_name', '').strip()
        country = request.POST.get('country', 'United States')
        currency_code = request.POST.get('currency_code', 'USD')
        currency_symbol = request.POST.get('currency_symbol', '$')

        if form.is_valid() and company_name:
            with transaction.atomic():
                user = form.save()
                org = Organization.objects.create(
                    name=company_name,
                    country=country,
                    currency_code=currency_code,
                    currency_symbol=currency_symbol
                )
                UserProfile.objects.create(
                    user=user,
                    organization=org,
                    role='OWNER'
                )

                # Clear guest flags if upgrading from guest
                request.session.pop('is_guest', None)
                request.session.pop('guest_expiry', None)

                login(request, user)
                messages.success(request, "Account created successfully! Welcome to StockFlow.")
                return redirect('onboarding')
        else:
            if not company_name:
                messages.error(request, "Company name is required.")
            else:
                messages.error(request, "Please correct the registration errors below.")
    else:
        form = UserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})

def logout_view(request):
    logout(request)
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def onboarding_view(request):
    org = request.organization
    if not org:
        org = Organization.objects.create(name=f"{request.user.username}'s Business")
        request.user_profile.organization = org
        request.user_profile.save()

    if request.method == 'POST':
        if request.session.get('is_guest', False):
            messages.warning(request, "Organization settings are locked in Guest Mode. Please create a full account.")
            return redirect('dashboard')

        org.name = request.POST.get('name', org.name)
        org.country = request.POST.get('country', org.country)
        org.currency_code = request.POST.get('currency_code', org.currency_code)
        org.currency_symbol = request.POST.get('currency_symbol', org.currency_symbol)
        org.currency_position = request.POST.get('currency_position', org.currency_position)
        org.date_format = request.POST.get('date_format', org.date_format)
        org.number_format = request.POST.get('number_format', org.number_format)
        org.timezone = request.POST.get('timezone', org.timezone)
        org.tax_name = request.POST.get('tax_name', org.tax_name)
        org.tax_rate = request.POST.get('tax_rate', org.tax_rate)
        org.tax_id_label = request.POST.get('tax_id_label', org.tax_id_label)
        org.tax_id_value = request.POST.get('tax_id_value', org.tax_id_value)
        org.address = request.POST.get('address', org.address)
        org.phone = request.POST.get('phone', org.phone)
        org.email = request.POST.get('email', org.email)
        org.save()

        messages.success(request, "Organization settings saved successfully!")
        return redirect('dashboard')

    return render(request, 'accounts/onboarding.html', {'org': org})

@login_required
def settings_view(request):
    org = request.organization
    if request.method == 'POST':
        if request.session.get('is_guest', False):
            messages.warning(request, "Settings modifications are restricted in Guest Mode. Please register for a full account.")
            return redirect('settings')

        action = request.POST.get('action')
        if action == 'update_profile':
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            request.user_profile.phone = request.POST.get('phone', '')
            request.user_profile.save()
            messages.success(request, "Profile updated.")
        elif action == 'update_org':
            org.name = request.POST.get('name', org.name)
            org.country = request.POST.get('country', org.country)
            org.currency_code = request.POST.get('currency_code', org.currency_code)
            org.currency_symbol = request.POST.get('currency_symbol', org.currency_symbol)
            org.currency_position = request.POST.get('currency_position', org.currency_position)
            org.date_format = request.POST.get('date_format', org.date_format)
            org.number_format = request.POST.get('number_format', org.number_format)
            org.timezone = request.POST.get('timezone', org.timezone)
            org.tax_name = request.POST.get('tax_name', org.tax_name)
            org.tax_rate = request.POST.get('tax_rate', org.tax_rate)
            org.tax_id_label = request.POST.get('tax_id_label', org.tax_id_label)
            org.tax_id_value = request.POST.get('tax_id_value', org.tax_id_value)
            org.address = request.POST.get('address', org.address)
            org.phone = request.POST.get('phone', org.phone)
            org.email = request.POST.get('email', org.email)
            org.website = request.POST.get('website', org.website)
            org.save()
            messages.success(request, "Business settings updated.")
        return redirect('settings')

    return render(request, 'accounts/settings.html', {'org': org})
