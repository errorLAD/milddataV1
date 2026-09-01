from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib import messages
import datetime
import uuid

from .models import Organization, User, AuditLog, Notification, GuestSession
from .utils.security import guest_restricted
from apps.properties.models import Property, Unit
from apps.tenants.models import TenantProfile
from apps.leases.models import Lease
from apps.finance.models import RentInvoice, Payment, Expense
from apps.maintenance.models import MaintenanceTicket

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Audit Log
            if user.organization:
                AuditLog.objects.create(
                    organization=user.organization,
                    user=user,
                    action="User Login",
                    entity_type="User",
                    entity_id=str(user.id),
                    ip_address=request.META.get('REMOTE_ADDR')
                )

            # Redirect based on role
            if user.role == User.ROLE_TENANT:
                return redirect('tenant_pwa')
            elif user.role == User.ROLE_PROPERTY_OWNER:
                return redirect('owner_dashboard')
            return redirect('dashboard')
        else:
            error_message = "Invalid authentication credentials. Please check your details and try again."
            
    return render(request, 'auth/login.html', {'error': error_message})

def guest_login_view(request):
    demo_org, _ = Organization.objects.get_or_create(
        slug='propflow-partners',
        defaults={'name': 'PropFlow Demo Portfolio', 'plan': Organization.PLAN_PROFESSIONAL, 'is_demo_org': True}
    )

    guest_id = str(uuid.uuid4())[:8]
    guest_user = User.objects.create_user(
        username=f"guest_{guest_id}",
        email=f"guest_{guest_id}@propflow.demo",
        password=f"GuestPass_{guest_id}",
        first_name="Guest",
        last_name="Explorer",
        organization=demo_org,
        role=User.ROLE_GUEST
    )

    expires_at = timezone.now() + datetime.timedelta(hours=24)
    GuestSession.objects.create(
        guest_user=guest_user,
        expires_at=expires_at
    )

    login(request, guest_user)
    messages.info(request, "👋 Welcome to PropFlow Guest Mode! You have read-only access to explore demo properties, dashboard, and AI assistant.")
    return redirect('dashboard')

@login_required
def guest_upgrade_view(request):
    if request.method == 'POST':
        org_name = request.POST.get('org_name')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        slug = f"org-{uuid.uuid4().hex[:6]}"
        new_org = Organization.objects.create(name=org_name, slug=slug, plan=Organization.PLAN_PROFESSIONAL)

        user = request.user
        user.organization = new_org
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = email
        user.set_password(password)
        user.role = User.ROLE_PROPERTY_MANAGER
        user.save()

        GuestSession.objects.filter(guest_user=user).delete()
        login(request, user)

        messages.success(request, f"🎉 Account upgraded! Welcome to PropFlow, {user.first_name}!")
        return redirect('dashboard')

    return render(request, 'auth/guest_upgrade.html')

def logout_view(request):
    logout(request)
    return redirect('landing_page')

@login_required
def dashboard(request):
    user = request.user
    
    if user.role == User.ROLE_TENANT:
        return redirect('tenant_pwa')
    elif user.role == User.ROLE_PROPERTY_OWNER:
        return redirect('owner_dashboard')

    org = user.organization
    if not org:
        return render(request, 'dashboard/overview.html', {'org_name': 'No Organization'})

    properties = Property.objects.filter(organization=org)
    total_properties = properties.count()
    
    units = Unit.objects.filter(property__organization=org)
    total_units = units.count()
    occupied_units = units.filter(status=Unit.STATUS_OCCUPIED).count()
    vacant_units = units.filter(status=Unit.STATUS_VACANT).count()
    maint_units = units.filter(status=Unit.STATUS_MAINTENANCE).count()
    occupancy_pct = round((occupied_units / total_units * 100), 1) if total_units > 0 else 0

    # Rent collection metrics
    invoices = RentInvoice.objects.filter(organization=org)
    total_rent_expected = sum(inv.total_due for inv in invoices)
    total_rent_collected = sum(inv.total_paid for inv in invoices)
    outstanding_rent = total_rent_expected - total_rent_collected
    overdue_invoices_count = invoices.filter(status=RentInvoice.STATUS_OVERDUE).count()

    # Expenses & Net Income
    expenses = Expense.objects.filter(organization=org)
    total_expenses = sum(exp.amount for exp in expenses)
    net_income = total_rent_collected - total_expenses

    # Aggregated Expense Categories
    category_totals = {}
    for exp in expenses:
        cat_name = exp.get_category_display()
        category_totals[cat_name] = category_totals.get(cat_name, 0) + float(exp.amount)
    
    expense_categories = [{'name': k, 'total': v} for k, v in category_totals.items()]

    # Maintenance
    tickets = MaintenanceTicket.objects.filter(organization=org)
    open_tickets = tickets.filter(Q(status=MaintenanceTicket.STATUS_NEW) | Q(status=MaintenanceTicket.STATUS_IN_PROGRESS) | Q(status=MaintenanceTicket.STATUS_ASSIGNED)).count()
    
    # Expiring Leases
    today = datetime.date.today()
    in_30_days = today + datetime.timedelta(days=30)
    expiring_leases = Lease.objects.filter(
        organization=org, 
        status=Lease.STATUS_ACTIVE, 
        end_date__gte=today, 
        end_date__lte=in_30_days
    )

    # Recent activities (audit logs) & Recent Payments
    recent_activities = AuditLog.objects.filter(organization=org)[:8]
    recent_payments = Payment.objects.filter(organization=org)[:6]

    # Revenue chart data
    chart_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    revenue_data = [12500, 14200, 13800, 15600, 16200, float(total_rent_collected)]
    expense_data = [3100, 4200, 2900, 3800, 4100, float(total_expenses)]

    context = {
        'total_properties': total_properties,
        'properties': properties,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacant_units': vacant_units,
        'maint_units': maint_units,
        'occupancy_pct': occupancy_pct,
        'total_rent_collected': total_rent_collected,
        'outstanding_rent': outstanding_rent,
        'overdue_invoices_count': overdue_invoices_count,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'open_tickets_count': open_tickets,
        'expiring_leases_count': expiring_leases.count(),
        'expiring_leases': expiring_leases,
        'recent_activities': recent_activities,
        'recent_payments': recent_payments,
        'expense_categories': expense_categories,
        'chart_months': chart_months,
        'revenue_data': revenue_data,
        'expense_data': expense_data,
    }
    return render(request, 'dashboard/overview.html', context)

@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    org = request.user.organization
    results = []

    # Search Properties
    props = Property.objects.filter(organization=org, name__icontains=query)[:3]
    for p in props:
        results.append({
            'category': 'Property',
            'title': p.name,
            'subtitle': f"{p.city}, {p.state} • {p.get_property_type_display()}",
            'url': f"/properties/{p.id}/"
        })

    # Search Units
    units = Unit.objects.filter(property__organization=org, unit_number__icontains=query)[:3]
    for u in units:
        results.append({
            'category': 'Unit',
            'title': f"Unit {u.unit_number}",
            'subtitle': f"{u.property.name} • ${u.monthly_rent}/mo",
            'url': f"/properties/{u.property.id}/"
        })

    # Search Tenants
    tenants = User.objects.filter(organization=org, role=User.ROLE_TENANT).filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
    )[:3]
    for t in tenants:
        results.append({
            'category': 'Tenant',
            'title': t.get_full_name() or t.username,
            'subtitle': t.email,
            'url': f"/tenants/{t.id}/"
        })

    # Search Tickets
    tickets = MaintenanceTicket.objects.filter(organization=org, title__icontains=query)[:3]
    for t in tickets:
        results.append({
            'category': 'Maintenance',
            'title': f"Ticket #{t.id}: {t.title}",
            'subtitle': f"{t.property.name} • {t.get_status_display()}",
            'url': f"/maintenance/{t.id}/"
        })

    return JsonResponse({'results': results})

@login_required
def audit_logs(request):
    org = request.user.organization
    logs = AuditLog.objects.filter(organization=org)
    return render(request, 'core/audit_logs.html', {'logs': logs})

@login_required
def notifications_list(request):
    org = request.user.organization
    notifications = Notification.objects.filter(recipient=request.user)
    if request.method == 'POST':
        notifications.update(is_read=True)
        return redirect('notifications')
    return render(request, 'core/notifications.html', {'notifications': notifications})
