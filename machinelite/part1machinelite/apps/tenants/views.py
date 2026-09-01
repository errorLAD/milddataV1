import uuid
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q
from datetime import date, timedelta

from apps.machines.models import Machine, MeterLog
from apps.fuel.models import FuelLog
from apps.maintenance.models import MaintenanceLog
from apps.documents.models import MachineDocument
from apps.finance.models import RevenueLog, ExpenseLog
from apps.operators.models import Operator
from apps.projects.models import Project, MachineAllocation
from apps.tenants.models import Organization, UserProfile

def dashboard_view(request):
    """
    Renders comprehensive executive dashboard for both Authenticated Users and Guests in safe read-only demo mode.
    Includes machine category breakdown, project allocations, operator roster, P&L ranking, service watchlists, and document expiries.
    """
    is_guest = getattr(request, 'is_guest', False)
    if not request.user.is_authenticated and not is_guest:
        return redirect('login')

    tenant = request.tenant
    if not tenant:
        return render(request, 'dashboard/index.html', {'error': 'No organization context found.'})

    machines = Machine.objects.filter(organization=tenant)
    total_machines = machines.count()
    working_machines = machines.filter(status='working').count()
    idle_machines = machines.filter(status='idle').count()
    breakdown_machines = machines.filter(status='breakdown').count()
    maintenance_machines = machines.filter(status='maintenance').count()

    total_fleet_value = float(machines.aggregate(s=Sum('estimated_value'))['s'] or 0)

    # 1. Document Expiry Alerts
    today = date.today()
    expired_docs = MachineDocument.objects.filter(organization=tenant, expiry_date__lt=today)
    expiring_soon_docs = MachineDocument.objects.filter(organization=tenant, expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30))

    # 2. Financial Metrics
    rev_total = float(RevenueLog.objects.filter(organization=tenant).aggregate(s=Sum('amount'))['s'] or 0)
    fuel_total = float(FuelLog.objects.filter(organization=tenant).aggregate(s=Sum('total_cost'))['s'] or 0)
    maint_total = float(MaintenanceLog.objects.filter(organization=tenant).aggregate(s=Sum('cost'))['s'] or 0)
    exp_total = float(ExpenseLog.objects.filter(organization=tenant).aggregate(s=Sum('amount'))['s'] or 0)

    total_costs = fuel_total + maint_total + exp_total
    net_profit = rev_total - total_costs
    profit_margin = (net_profit / rev_total * 100) if rev_total > 0 else 0

    # 3. Category Breakdown Data
    category_counts = []
    for cat_code, cat_label in Machine.CATEGORY_CHOICES:
        cat_qs = machines.filter(category=cat_code)
        c_count = cat_qs.count()
        if c_count > 0:
            c_val = float(cat_qs.aggregate(s=Sum('estimated_value'))['s'] or 0)
            category_counts.append({
                'code': cat_code,
                'label': cat_label,
                'count': c_count,
                'value': c_val,
                'percentage': round((c_count / total_machines * 100), 1) if total_machines > 0 else 0
            })

    # 4. Project Site Deployments
    projects = Project.objects.filter(organization=tenant)
    project_deployments = []
    for p in projects:
        allocs = MachineAllocation.objects.filter(organization=tenant, project=p, is_active=True)
        project_deployments.append({
            'project': p,
            'machine_count': allocs.count(),
            'allocations': allocs[:4],
        })

    # 5. Active Operators Roster
    operators = Operator.objects.filter(organization=tenant, status='active')[:6]

    # 6. Machine Profitability Ranking (Top Earners)
    machine_profit_ranking = []
    for m in machines:
        m_rev = float(RevenueLog.objects.filter(organization=tenant, machine=m).aggregate(s=Sum('amount'))['s'] or 0)
        m_fuel = float(FuelLog.objects.filter(organization=tenant, machine=m).aggregate(s=Sum('total_cost'))['s'] or 0)
        m_maint = float(MaintenanceLog.objects.filter(organization=tenant, machine=m).aggregate(s=Sum('cost'))['s'] or 0)
        m_profit = m_rev - (m_fuel + m_maint)
        machine_profit_ranking.append({
            'machine': m,
            'revenue': m_rev,
            'fuel': m_fuel,
            'maint': m_maint,
            'net_profit': m_profit,
        })
    machine_profit_ranking.sort(key=lambda x: x['net_profit'], reverse=True)

    # 7. Service Watchlist (Approaching scheduled service <= 50 HRs)
    service_watchlist = []
    for m in machines:
        last_m = MaintenanceLog.objects.filter(organization=tenant, machine=m).order_by('-date').first()
        if last_m and last_m.next_service_meter:
            rem = last_m.next_service_meter - m.current_meter
            if rem <= 100:
                service_watchlist.append({
                    'machine': m,
                    'current_meter': m.current_meter,
                    'target_meter': last_m.next_service_meter,
                    'remaining': round(rem, 1),
                })
    service_watchlist.sort(key=lambda x: x['remaining'])

    # 8. Fuel Anomaly Flags
    abnormal_fuel = FuelLog.objects.filter(organization=tenant, is_abnormal_flag=True)[:5]
    recent_meters = MeterLog.objects.filter(organization=tenant)[:6]

    context = {
        'total_machines': total_machines,
        'working_machines': working_machines,
        'idle_machines': idle_machines,
        'breakdown_machines': breakdown_machines,
        'maintenance_machines': maintenance_machines,
        'total_fleet_value': total_fleet_value,
        
        'expired_docs_count': expired_docs.count(),
        'expiring_docs_count': expiring_soon_docs.count(),
        'expired_docs': expired_docs[:5],
        'expiring_soon_docs': expiring_soon_docs[:5],
        
        'rev_total': rev_total,
        'fuel_total': fuel_total,
        'maint_total': maint_total,
        'total_costs': total_costs,
        'net_profit': net_profit,
        'profit_margin': round(profit_margin, 1),
        
        'category_counts': category_counts,
        'project_deployments': project_deployments,
        'operators': operators,
        'machine_profit_ranking': machine_profit_ranking[:5],
        'service_watchlist': service_watchlist,
        
        'abnormal_fuel': abnormal_fuel,
        'recent_meters': recent_meters,
        'machines': machines[:10],
    }
    return render(request, 'dashboard/index.html', context)

def guest_login_view(request):
    """
    Creates a temporary Guest Session with a unique ID and automatic timeout.
    """
    request.session.flush()
    request.session['is_guest'] = True
    request.session['guest_id'] = str(uuid.uuid4())[:8]
    request.session.set_expiry(3600)
    messages.info(request, "👋 You are currently browsing in Guest Mode. Data modifications are disabled.")
    return redirect('dashboard')

def upgrade_account_view(request):
    """
    Allows guest users or new accounts to register a full organization account.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        org_name = request.POST.get('organization_name', '').strip()
        
        if form.is_valid() and org_name:
            user = form.save()
            code = f"ORG-{str(uuid.uuid4())[:6].upper()}"
            org = Organization.objects.create(name=org_name, code=code)
            UserProfile.objects.create(user=user, organization=org, role='admin')
            
            request.session.flush()
            login(request, user)
            messages.success(request, f"🎉 Welcome! Your enterprise organization '{org_name}' has been created.")
            return redirect('dashboard')
        else:
            messages.error(request, "Registration failed. Please check form errors.")
    else:
        form = UserCreationForm()
    return render(request, 'registration/upgrade.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            request.session.flush()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password credentials.")
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    request.session.flush()
    logout(request)
    return redirect('login')
