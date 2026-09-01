import uuid
import time
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views import View
from django.contrib.auth.models import User
from core.audit import log_security_event
from .models import Business, UserProfile
from .forms import RegistrationForm, LoginForm


def populate_guest_demo_data(business):
    """
    Populates rich demo data for the guest sandbox business if it's empty.
    """
    try:
        from customers.models import Customer
        from sales.models import Sale, SaleItem
        from products.models import Product
        from udhaar.models import Udhaar
        from django.utils import timezone
        import datetime

        if Customer.objects.filter(business=business).exists():
            return

        # 1. Create Demo Products
        p1 = Product.objects.create(
            business=business,
            name="Industrial Steel Pipes (100m)",
            sku="PROD-STEEL-100",
            category="Industrial Supplies",
            selling_price=45000.00,
            stock_quantity=50
        )
        p2 = Product.objects.create(
            business=business,
            name="Electrical Conduit Cables (Pack of 50)",
            sku="PROD-CABLE-50",
            category="Electrical",
            selling_price=18500.00,
            stock_quantity=120
        )

        # 2. Create Demo Customers
        c1 = Customer.objects.create(
            business=business,
            name="Apex Engineering Solutions",
            phone="9876543210",
            email="accounts@apexeng.com",
            address="102 Tech Park, Phase 2, Industrial Estate",
            credit_limit=250000.00
        )
        c2 = Customer.objects.create(
            business=business,
            name="Zenith Infrastructure Pvt Ltd",
            phone="9876543211",
            email="billing@zenithinfra.com",
            address="45 Commercial Plaza, Sector 18",
            credit_limit=500000.00
        )

        # 3. Create Demo Invoices
        today = timezone.now().date()
        s1 = Sale.objects.create(
            business=business,
            invoice_number="INV-GUEST-001",
            customer=c1,
            total_amount=45000.00,
            paid_amount=0.00,
            udhaar_amount=45000.00,
            payment_method="Udhaar / Credit"
        )
        SaleItem.objects.create(sale=s1, product=p1, product_name=p1.name, quantity=1, unit_price=45000.00, subtotal=45000.00)

        s2 = Sale.objects.create(
            business=business,
            invoice_number="INV-GUEST-002",
            customer=c2,
            total_amount=37000.00,
            paid_amount=10000.00,
            udhaar_amount=27000.00,
            payment_method="Udhaar / Credit"
        )
        SaleItem.objects.create(sale=s2, product=p2, product_name=p2.name, quantity=2, unit_price=18500.00, subtotal=37000.00)

        # 4. Create Demo Udhaars / Collections
        Udhaar.objects.create(
            business=business,
            customer=c1,
            sale=s1,
            total_amount=45000.00,
            paid_amount=0.00,
            remaining_amount=45000.00,
            due_date=today - datetime.timedelta(days=2),
            status="Overdue",
            notes="Overdue demo collection for testing workflows."
        )
        Udhaar.objects.create(
            business=business,
            customer=c2,
            sale=s2,
            total_amount=37000.00,
            paid_amount=10000.00,
            remaining_amount=27000.00,
            due_date=today + datetime.timedelta(days=5),
            status="Due",
            notes="Upcoming payment promise."
        )
    except Exception as e:
        print(f"Error initializing guest demo data: {e}")


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = RegistrationForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        was_guest = request.session.get('is_guest', False)
        form = RegistrationForm(request.POST)
        if form.is_valid():
            b_name = form.cleaned_data['business_name']
            owner_name = form.cleaned_data['owner_name']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            country = form.cleaned_data.get('country', 'US')

            # Create Business
            business = Business.objects.create(
                name=b_name,
                owner_name=owner_name,
                phone=phone,
                email=email
            )

            # Create User
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=owner_name
            )

            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                business=business,
                role='Owner',
                phone=phone
            )

            # Initialize Default Business Settings
            try:
                from settings_app.models import BusinessSettings
                from whatsapp.models import WhatsAppMessageTemplate

                b_settings, _ = BusinessSettings.objects.get_or_create(
                    business=business,
                    defaults={
                        'upi_id': f"{phone}@upi",
                        'payee_name': b_name,
                        'reminder_before_due_days': 2,
                        'reminder_on_due_date': True,
                        'followup_frequency_days': 3,
                    }
                )
                b_settings.apply_country_defaults(country)
                b_settings.save()

                WhatsAppMessageTemplate.objects.get_or_create(
                    business=business,
                    trigger_type='Due Reminder',
                    defaults={
                        'title': 'Friendly Due Reminder',
                        'content': 'Namaste {{customer_name}}, {{business_name}} se aapka balance {{amount}} due hai on {{due_date}}.'
                    }
                )
            except Exception:
                pass

            # Flush guest session flag
            request.session.flush()
            login(request, user)

            event_type = 'GUEST_UPGRADE' if was_guest else 'LOGIN_SUCCESS'
            log_security_event(event_type, request, user=user, details=f"Registered business '{b_name}'")

            messages.success(request, f"Welcome to NextSlot B2B Collections, {b_name}!")
            return redirect('dashboard:index')

        return render(request, 'accounts/register.html', {'form': form})


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_superuser or request.user.is_staff:
                return redirect('platform_admin:dashboard')
            return redirect('dashboard:index')
        form = LoginForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                request.session.flush()
                login(request, user)
                log_security_event('LOGIN_SUCCESS', request, user=user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                if user.is_superuser or user.is_staff:
                    return redirect('platform_admin:dashboard')
                return redirect('dashboard:index')
            else:
                log_security_event('LOGIN_FAILED', request, username=username, details="Invalid password")
                messages.error(request, "Invalid username or password.")
        return render(request, 'accounts/login.html', {'form': form})


class LogoutView(View):
    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        log_security_event('LOGOUT', request, user=user)
        logout(request)
        request.session.flush()
        messages.info(request, "You have been logged out.")
        return redirect('accounts:login')


class GuestLoginView(View):
    """
    Initializes a temporary guest session with access to sandbox demo data.
    """
    def get(self, request):
        # 1. Clear any active user session
        if request.user.is_authenticated:
            logout(request)

        request.session.flush()

        # 2. Setup guest session keys
        request.session['is_guest'] = True
        request.session['guest_session_id'] = str(uuid.uuid4())
        request.session['guest_created_at'] = time.time()
        request.session.set_expiry(7200)  # 2 Hours Expiry

        # 3. Ensure Demo Sandbox Business exists and is populated
        guest_b, _ = Business.objects.get_or_create(
            name="Demo Guest Business",
            defaults={
                'owner_name': 'Guest User',
                'phone': '9999999999',
                'email': 'guest@demo.local',
                'address': 'Demo Sandbox Location',
                'is_active': True
            }
        )
        populate_guest_demo_data(guest_b)

        log_security_event('GUEST_LOGIN', request, details=f"Guest Session ID: {request.session['guest_session_id']}")
        messages.success(request, "Entered Guest Mode! You have 2 hours to explore interactive demo features.")
        return redirect('dashboard:index')


class UpgradeGuestView(View):
    """
    Allows a guest user to upgrade to a full account easily.
    """
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'accounts/upgrade_guest.html', {'form': form})

    def post(self, request):
        return RegisterView().post(request)

