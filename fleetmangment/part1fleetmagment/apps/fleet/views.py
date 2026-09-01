from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
import csv
import random
from datetime import timedelta

from .models import (
    Organization, User, Vehicle, Trip, GPSLog, Geofence, GeofenceLog,
    MaintenanceRecord, FuelLog, Expense, Document, InspectionChecklist,
    DispatchJob, Alert, AuditLog, Subscription
)

# Helper function to get user's organization
def get_user_org(request):
    if hasattr(request.user, 'organization') and request.user.organization:
        return request.user.organization
    return Organization.objects.first()

# Auth Views
def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'DRIVER':
            return redirect('pwa_home')
        return redirect('dashboard')
        
    error = None
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(username=u, password=p)
        if user:
            login(request, user)
            AuditLog.objects.create(
                organization=user.organization,
                user=user,
                action="User logged into system",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            if user.role == 'DRIVER':
                return redirect('pwa_home')
            return redirect('dashboard')
        else:
            error = "Invalid username or password."
    return render(request, 'auth/login.html', {'error': error})


def guest_login_view(request):
    demo_org, _ = Organization.objects.get_or_create(
        slug='public-demo-fleet',
        defaults={'name': 'Public Demo Fleet Corp', 'plan_name': 'DEMO'}
    )
    guest_user, created = User.objects.get_or_create(
        username='guest_demo',
        defaults={
            'organization': demo_org,
            'role': 'VIEWER',
            'first_name': 'Guest',
            'last_name': 'User',
            'email': 'guest@demofleet.com'
        }
    )
    if created:
        guest_user.set_password('guestdemo123!')
        guest_user.save()

    login(request, guest_user)
    request.session['is_guest'] = True
    request.session.set_expiry(7200) # 2 hours auto-expiry

    AuditLog.objects.create(
        organization=demo_org,
        user=guest_user,
        action="Guest session initiated (Public Demo Access)",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    return redirect('dashboard')


def logout_view(request):
    logout(request)
    return redirect('login')


# 1. Owner / Admin Dashboard
# 1. Owner / Admin Dashboard
@login_required
def dashboard_view(request):
    org = get_user_org(request)
    vehicles = Vehicle.objects.filter(organization=org)
    
    total_vehicles = vehicles.count()
    active_vehicles = vehicles.exclude(status='OFFLINE').count()
    moving_vehicles = vehicles.filter(status='MOVING').count()
    idle_vehicles = vehicles.filter(status='IDLE').count()
    stopped_vehicles = vehicles.filter(status='STOPPED').count()
    offline_vehicles = vehicles.filter(status='OFFLINE').count()
    maintenance_vehicles = vehicles.filter(status='MAINTENANCE').count()
    
    active_trips = Trip.objects.filter(organization=org, status__in=['STARTED', 'IN_PROGRESS']).count()
    active_trips_list = Trip.objects.filter(organization=org, status__in=['STARTED', 'IN_PROGRESS'])[:4]
    
    # Calculate today's telemetry
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_distance = Trip.objects.filter(organization=org, start_time__gte=today_start).aggregate(s=Sum('distance_km'))['s'] or 48.5
    today_fuel = FuelLog.objects.filter(organization=org, date__gte=today_start.date()).aggregate(s=Sum('fuel_quantity_liters'))['s'] or 140.0
    today_idle_hrs = round(idle_vehicles * 0.8, 1)

    # Expenses breakdown
    this_month_start = today_start.replace(day=1)
    fuel_expenses = float(FuelLog.objects.filter(organization=org, date__gte=this_month_start).aggregate(s=Sum('total_cost'))['s'] or 161.00)
    maint_expenses = float(MaintenanceRecord.objects.filter(organization=org, service_date__gte=this_month_start).aggregate(s=Sum('total_cost'))['s'] or 360.00)
    other_expenses = float(Expense.objects.filter(organization=org, date__gte=this_month_start).aggregate(s=Sum('amount'))['s'] or 45.00)
    total_monthly_spend = round(fuel_expenses + maint_expenses + other_expenses, 2)
    
    cost_per_km = round(total_monthly_spend / max(1.0, today_distance * 30), 2) or 0.42
    utilization_pct = int((active_vehicles / max(1, total_vehicles)) * 100) if total_vehicles > 0 else 85

    # Documents expiring
    expiring_docs_list = Document.objects.filter(organization=org, expiry_date__lte=timezone.now().date() + timedelta(days=30))[:4]
    expiring_docs_count = expiring_docs_list.count()
    
    # Upcoming Maintenance
    upcoming_maint_list = MaintenanceRecord.objects.filter(organization=org, status__in=['SCHEDULED', 'IN_PROGRESS'])[:4]
    
    # Recent alerts & activity
    recent_alerts = Alert.objects.filter(organization=org)[:4]
    recent_activity = AuditLog.objects.filter(organization=org)[:5]

    # Health score breakdown tiers
    health_scores = [v.health_score_breakdown['score'] for v in vehicles] if vehicles.exists() else [92, 85, 100, 78, 90]
    avg_fleet_health = int(sum(health_scores) / len(health_scores)) if health_scores else 90

    health_tiers = {
        'excellent': len([s for s in health_scores if s >= 80]),
        'good': len([s for s in health_scores if 60 <= s < 80]),
        'average': len([s for s in health_scores if 40 <= s < 60]),
        'poor': len([s for s in health_scores if 20 <= s < 40]),
        'critical': len([s for s in health_scores if s < 20]),
    }

    # Map markers JSON for inline live map
    vehicles_map_data = []
    for v in vehicles:
        vehicles_map_data.append({
            'id': v.id,
            'code': v.vehicle_code,
            'reg': v.registration_number,
            'type': v.vehicle_type,
            'status': v.status,
            'lat': v.last_lat or 28.6139,
            'lng': v.last_lng or 77.2090,
            'speed': v.last_speed,
            'driver': v.current_driver.get_full_name() if v.current_driver else 'Unassigned',
        })

    # AI Auto Insights
    ai_insights = []
    suspicious_fuels = FuelLog.objects.filter(organization=org, is_suspicious=True).count()
    if suspicious_fuels > 0:
        ai_insights.append({
            'type': 'warning',
            'title': 'Suspicious Fuel Entry Flagged',
            'desc': f'{suspicious_fuels} fuel refill entry exceeds expected L/100km rate by >30%.'
        })
    if maintenance_vehicles > 0:
        ai_insights.append({
            'type': 'info',
            'title': 'Active Garage Maintenance',
            'desc': f'{maintenance_vehicles} unit(s) currently undergoing repair in workshop.'
        })
    if expiring_docs_count > 0:
        ai_insights.append({
            'type': 'danger',
            'title': 'Compliance Document Expiry Notice',
            'desc': f'{expiring_docs_count} document(s) expiring within 30 days.'
        })
    if not ai_insights:
        ai_insights.append({
            'type': 'success',
            'title': 'Fleet Operating Nominally',
            'desc': 'No severe diagnostic anomalies or efficiency bottlenecks detected.'
        })

    context = {
        'org': org,
        'total_vehicles': total_vehicles,
        'active_vehicles': active_vehicles,
        'moving_vehicles': moving_vehicles,
        'idle_vehicles': idle_vehicles,
        'stopped_vehicles': stopped_vehicles,
        'offline_vehicles': offline_vehicles,
        'maintenance_vehicles': maintenance_vehicles,
        'active_trips': active_trips,
        'active_trips_list': active_trips_list,
        'today_distance': round(today_distance, 1),
        'today_fuel': round(today_fuel, 1),
        'today_idle_hrs': today_idle_hrs,
        'fuel_expenses': fuel_expenses,
        'maint_expenses': maint_expenses,
        'other_expenses': other_expenses,
        'total_monthly_spend': total_monthly_spend,
        'cost_per_km': cost_per_km,
        'utilization_pct': utilization_pct,
        'expiring_docs_count': expiring_docs_count,
        'expiring_docs_list': expiring_docs_list,
        'upcoming_maint_list': upcoming_maint_list,
        'recent_alerts': recent_alerts,
        'recent_activity': recent_activity,
        'avg_fleet_health': avg_fleet_health,
        'health_tiers': health_tiers,
        'ai_insights': ai_insights,
        'vehicles': vehicles[:6],
        'vehicles_map_json': json.dumps(vehicles_map_data),
    }
    return render(request, 'fleet/dashboard.html', context)



# 2. Live Fleet Tracking
@login_required
def tracking_view(request):
    org = get_user_org(request)
    status_filter = request.GET.get('status', 'ALL')
    vehicles_qs = Vehicle.objects.filter(organization=org)
    
    if status_filter != 'ALL':
        vehicles_qs = vehicles_qs.filter(status=status_filter)
        
    vehicles_data = []
    for v in vehicles_qs:
        vehicles_data.append({
            'id': v.id,
            'code': v.vehicle_code,
            'reg': v.registration_number,
            'type': v.vehicle_type,
            'type_display': v.get_vehicle_type_display(),
            'status': v.status,
            'status_display': v.get_status_display(),
            'driver': v.current_driver.get_full_name() if v.current_driver else 'Unassigned',
            'lat': v.last_lat or 28.6139, # Default Delhi / standard lat
            'lng': v.last_lng or 77.2090,
            'speed': v.last_speed,
            'heading': v.last_heading,
            'updated': v.last_gps_update.strftime('%H:%M:%S') if v.last_gps_update else 'N/A',
            'battery': v.battery_level,
            'is_stale': v.is_stale_gps,
        })
        
    context = {
        'vehicles_json': json.dumps(vehicles_data),
        'status_filter': status_filter,
        'vehicles': vehicles_qs,
    }
    return render(request, 'fleet/tracking.html', context)


# 3. Trip Management
@login_required
def trips_list_view(request):
    org = get_user_org(request)
    
    if request.method == 'POST':
        v_id = request.POST.get('vehicle_id')
        d_id = request.POST.get('driver_id')
        start_loc = request.POST.get('start_location', 'Origin Depot')
        dest_loc = request.POST.get('destination', 'Destination Site')
        
        vehicle = Vehicle.objects.filter(organization=org, id=v_id).first()
        driver = User.objects.filter(organization=org, id=d_id).first()
        
        if vehicle and driver:
            trip_code = f"TRIP-{timezone.now().strftime('%m%d%H%M%S')}"
            Trip.objects.create(
                organization=org,
                trip_id=trip_code,
                vehicle=vehicle,
                driver=driver,
                start_location=start_loc,
                destination=dest_loc,
                start_time=timezone.now(),
                status='STARTED'
            )
            vehicle.status = 'MOVING'
            vehicle.save()
            messages.success(request, f"Trip {trip_code} successfully created and assigned.")
            return redirect('trips_list')

    trips = Trip.objects.filter(organization=org).order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        trips = trips.filter(status=status_filter)
        
    vehicle_filter = request.GET.get('vehicle_id')
    if vehicle_filter:
        trips = trips.filter(vehicle_id=vehicle_filter)
        
    context = {
        'trips': trips,
        'vehicles': Vehicle.objects.filter(organization=org),
        'drivers': User.objects.filter(organization=org, role='DRIVER'),
    }
    return render(request, 'fleet/trips_list.html', context)


@login_required
def trip_detail_view(request, trip_id):
    org = get_user_org(request)
    trip = get_object_or_404(Trip, organization=org, id=trip_id)
    gps_logs = trip.gps_logs.all()
    
    route_coords = [[g.lat, g.lng] for g in gps_logs]
    
    context = {
        'trip': trip,
        'gps_logs': gps_logs,
        'route_json': json.dumps(route_coords),
    }
    return render(request, 'fleet/trip_detail.html', context)


# 4. Route Playback
@login_required
def route_playback_view(request):
    org = get_user_org(request)
    vehicle_id = request.GET.get('vehicle_id')
    vehicle = Vehicle.objects.filter(organization=org, id=vehicle_id).first() if vehicle_id else Vehicle.objects.filter(organization=org).first()
    
    gps_logs = GPSLog.objects.filter(vehicle=vehicle).order_by('recorded_at')[:300] if vehicle else []
    
    points_data = []
    for g in gps_logs:
        points_data.append({
            'lat': g.lat,
            'lng': g.lng,
            'speed': g.speed,
            'time': g.recorded_at.strftime('%H:%M:%S'),
            'battery': g.battery_level
        })
        
    context = {
        'vehicles': Vehicle.objects.filter(organization=org),
        'selected_vehicle': vehicle,
        'points_json': json.dumps(points_data),
    }
    return render(request, 'fleet/route_playback.html', context)


# 5. Geofencing Module
@login_required
def geofences_view(request):
    org = get_user_org(request)
    
    if request.method == 'POST':
        name = request.POST.get('name', 'New Zone')
        cat = request.POST.get('category', 'SITE')
        radius = float(request.POST.get('radius', 500))
        
        Geofence.objects.create(
            organization=org,
            name=name,
            category=cat,
            geofence_type='CIRCLE',
            center_lat=28.6139,
            center_lng=77.2090,
            radius_meters=radius
        )
        messages.success(request, f"Geofence zone '{name}' created successfully.")
        return redirect('geofences')

    geofences = Geofence.objects.filter(organization=org)
    logs = GeofenceLog.objects.filter(organization=org).order_by('-timestamp')[:20]
    
    geofences_data = []
    for g in geofences:
        geofences_data.append({
            'id': g.id,
            'name': g.name,
            'type': g.geofence_type,
            'category': g.get_category_display(),
            'lat': g.center_lat,
            'lng': g.center_lng,
            'radius': g.radius_meters,
            'coords': json.loads(g.coordinates_json or '[]')
        })

    context = {
        'geofences': geofences,
        'geofences_json': json.dumps(geofences_data),
        'logs': logs,
        'vehicles': Vehicle.objects.filter(organization=org)
    }
    return render(request, 'fleet/geofences.html', context)


# 6. Vehicles & Machines Management
@login_required
def vehicles_list_view(request):
    org = get_user_org(request)
    
    if request.method == 'POST':
        code = request.POST.get('vehicle_code')
        reg = request.POST.get('registration_number')
        vtype = request.POST.get('vehicle_type', 'TRUCK')
        brand = request.POST.get('brand', '')
        model = request.POST.get('model', '')
        d_id = request.POST.get('driver_id')
        
        driver = User.objects.filter(organization=org, id=d_id).first() if d_id else None
        
        v = Vehicle.objects.create(
            organization=org,
            vehicle_code=code,
            registration_number=reg,
            vehicle_type=vtype,
            brand=brand,
            model=model,
            current_driver=driver,
            last_lat=28.6139,
            last_lng=77.2090,
            last_gps_update=timezone.now()
        )
        messages.success(request, f"Vehicle {code} ({reg}) added to fleet catalog.")
        return redirect('vehicles_list')

    vehicles = Vehicle.objects.filter(organization=org)
    
    v_type = request.GET.get('type')
    if v_type:
        vehicles = vehicles.filter(vehicle_type=v_type)
        
    search_q = request.GET.get('q')
    if search_q:
        vehicles = vehicles.filter(Q(vehicle_code__icontains=search_q) | Q(registration_number__icontains=search_q) | Q(brand__icontains=search_q))

    context = {
        'vehicles': vehicles,
        'type_choices': Vehicle.TYPE_CHOICES,
        'drivers': User.objects.filter(organization=org, role='DRIVER')
    }
    return render(request, 'fleet/vehicles_list.html', context)


@login_required
def vehicle_detail_view(request, pk):
    org = get_user_org(request)
    vehicle = get_object_or_404(Vehicle, organization=org, id=pk)
    
    health_info = vehicle.health_score_breakdown
    maintenance_history = vehicle.maintenance_records.order_by('-service_date')
    fuel_history = vehicle.fuel_logs.order_by('-date')
    expense_history = vehicle.expenses.order_by('-date')
    documents = vehicle.documents.all()

    context = {
        'vehicle': vehicle,
        'health_info': health_info,
        'maintenance_history': maintenance_history,
        'fuel_history': fuel_history,
        'expense_history': expense_history,
        'documents': documents,
    }
    return render(request, 'fleet/vehicle_detail.html', context)


# 7. Driver Management
@login_required
def drivers_list_view(request):
    org = get_user_org(request)
    
    if request.method == 'POST':
        uname = request.POST.get('username')
        fname = request.POST.get('first_name', '')
        lname = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')
        lic = request.POST.get('license_number', '')
        
        u, created = User.objects.get_or_create(
            username=uname,
            defaults={
                'organization': org,
                'role': 'DRIVER',
                'first_name': fname,
                'last_name': lname,
                'phone': phone,
                'license_number': lic,
                'license_expiry': timezone.now().date() + timedelta(days=365)
            }
        )
        if created:
            u.set_password('driver123')
            u.save()
            messages.success(request, f"Driver {u.get_full_name() or uname} created successfully (Password: driver123).")
        return redirect('drivers_list')

    drivers = User.objects.filter(organization=org, role='DRIVER')
    
    context = {
        'drivers': drivers,
        'vehicles': Vehicle.objects.filter(organization=org)
    }
    return render(request, 'fleet/drivers_list.html', context)


# 8. Maintenance Management
@login_required
def maintenance_view(request):
    org = get_user_org(request)
    
    if request.method == 'POST':
        v_id = request.POST.get('vehicle_id')
        title = request.POST.get('title')
        mtype = request.POST.get('maintenance_type', 'ENGINE_SERVICE')
        workshop = request.POST.get('workshop_name', 'In-House Garage')
        cost = float(request.POST.get('total_cost', 0))
        
        vehicle = Vehicle.objects.filter(organization=org, id=v_id).first()
        if vehicle:
            MaintenanceRecord.objects.create(
                organization=org,
                vehicle=vehicle,
                title=title,
                maintenance_type=mtype,
                workshop_name=workshop,
                parts_cost=cost*0.6,
                labor_cost=cost*0.4,
                total_cost=cost,
                status='SCHEDULED',
                service_date=timezone.now().date()
            )
            messages.success(request, f"Maintenance task '{title}' scheduled for {vehicle.vehicle_code}.")
            return redirect('maintenance')

    records = MaintenanceRecord.objects.filter(organization=org).order_by('-service_date')
    
    status = request.GET.get('status')
    if status:
        records = records.filter(status=status)

    total_maint_cost = records.aggregate(s=Sum('total_cost'))['s'] or 0.0

    context = {
        'records': records,
        'total_cost': total_maint_cost,
        'vehicles': Vehicle.objects.filter(organization=org)
    }
    return render(request, 'fleet/maintenance.html', context)


# 9. Fuel Management
@login_required
def fuel_view(request):
    org = get_user_org(request)
    
    if request.method == 'POST':
        v_id = request.POST.get('vehicle_id')
        d_id = request.POST.get('driver_id')
        liters = float(request.POST.get('fuel_quantity_liters', 0))
        ppl = float(request.POST.get('price_per_liter', 1.15))
        station = request.POST.get('fuel_station', 'Highway Refill Station')
        
        vehicle = Vehicle.objects.filter(organization=org, id=v_id).first()
        driver = User.objects.filter(organization=org, id=d_id).first()
        
        if vehicle:
            FuelLog.objects.create(
                organization=org,
                vehicle=vehicle,
                driver=driver,
                fuel_quantity_liters=liters,
                price_per_liter=ppl,
                total_cost=liters * ppl,
                odometer_km=vehicle.mileage_km,
                fuel_station=station,
                date=timezone.now().date()
            )
            messages.success(request, f"Fuel entry of {liters}L logged for {vehicle.vehicle_code}.")
            return redirect('fuel')

    fuel_logs = FuelLog.objects.filter(organization=org).order_by('-date')
    
    total_liters = fuel_logs.aggregate(s=Sum('fuel_quantity_liters'))['s'] or 0.0
    total_fuel_cost = fuel_logs.aggregate(s=Sum('total_cost'))['s'] or 0.0
    suspicious_count = fuel_logs.filter(is_suspicious=True).count()

    context = {
        'fuel_logs': fuel_logs,
        'total_liters': round(total_liters, 1),
        'total_fuel_cost': round(total_fuel_cost, 2),
        'suspicious_count': suspicious_count,
        'vehicles': Vehicle.objects.filter(organization=org),
        'drivers': User.objects.filter(organization=org, role='DRIVER')
    }
    return render(request, 'fleet/fuel.html', context)


# 10. Fleet Expenses
@login_required
def expenses_view(request):
    org = get_user_org(request)
    
    if request.method == 'POST':
        v_id = request.POST.get('vehicle_id')
        cat = request.POST.get('category', 'OTHER')
        amt = float(request.POST.get('amount', 0))
        notes = request.POST.get('notes', '')
        
        vehicle = Vehicle.objects.filter(organization=org, id=v_id).first()
        
        Expense.objects.create(
            organization=org,
            vehicle=vehicle,
            category=cat,
            amount=amt,
            notes=notes,
            date=timezone.now().date()
        )
        messages.success(request, f"Expense of ${amt} logged.")
        return redirect('expenses')

    expenses = Expense.objects.filter(organization=org).order_by('-date')
    
    cat = request.GET.get('category')
    if cat:
        expenses = expenses.filter(category=cat)

    total_expense = expenses.aggregate(s=Sum('amount'))['s'] or 0.0

    context = {
        'expenses': expenses,
        'total_expense': round(total_expense, 2),
        'categories': Expense.CATEGORY_CHOICES,
        'vehicles': Vehicle.objects.filter(organization=org)
    }
    return render(request, 'fleet/expenses.html', context)


# 11. Document Management Vault
@login_required
def documents_view(request):
    org = get_user_org(request)
    
    if request.method == 'POST':
        title = request.POST.get('title', 'Document')
        dtype = request.POST.get('doc_type', 'REGISTRATION')
        v_id = request.POST.get('vehicle_id')
        expiry = request.POST.get('expiry_date', '2026-12-31')
        
        vehicle = Vehicle.objects.filter(organization=org, id=v_id).first()
        
        Document.objects.create(
            organization=org,
            vehicle=vehicle,
            title=title,
            doc_type=dtype,
            expiry_date=expiry
        )
        messages.success(request, f"Document '{title}' uploaded to vault.")
        return redirect('documents')

    documents = Document.objects.filter(organization=org).order_by('expiry_date')
    
    doc_filter = request.GET.get('status')
    if doc_filter == 'EXPIRED':
        documents = [d for d in documents if d.status() == 'EXPIRED']
    elif doc_filter == 'EXPIRING_SOON':
        documents = [d for d in documents if d.status() == 'EXPIRING_SOON']
    elif doc_filter == 'VALID':
        documents = [d for d in documents if d.status() == 'VALID']

    context = {
        'documents': documents,
        'vehicles': Vehicle.objects.filter(organization=org),
        'drivers': User.objects.filter(organization=org, role='DRIVER')
    }
    return render(request, 'fleet/documents.html', context)


# 12. Vehicle Inspection Checklists
@login_required
def inspections_view(request):
    org = get_user_org(request)
    inspections = InspectionChecklist.objects.filter(organization=org).order_by('-inspect_date')
    
    context = {
        'inspections': inspections,
        'vehicles': Vehicle.objects.filter(organization=org),
        'drivers': User.objects.filter(organization=org, role='DRIVER')
    }
    return render(request, 'fleet/inspections.html', context)


# 13. Dispatch / Jobs Management
@login_required
def dispatch_view(request):
    org = get_user_org(request)
    
    if request.method == 'POST':
        title = request.POST.get('title', 'Dispatch Task')
        d_id = request.POST.get('driver_id')
        v_id = request.POST.get('vehicle_id')
        dest = request.POST.get('destination_address', 'Site Address')
        instructions = request.POST.get('instructions', '')
        
        driver = User.objects.filter(organization=org, id=d_id).first()
        vehicle = Vehicle.objects.filter(organization=org, id=v_id).first()
        
        if driver and vehicle:
            job_code = f"JOB-{timezone.now().strftime('%m%d%H%M%S')}"
            DispatchJob.objects.create(
                organization=org,
                job_code=job_code,
                title=title,
                driver=driver,
                vehicle=vehicle,
                destination_address=dest,
                instructions=instructions,
                scheduled_time=timezone.now() + timedelta(hours=4),
                status='ASSIGNED'
            )
            messages.success(request, f"Job {job_code} dispatched to Driver {driver.get_full_name()}.")
            return redirect('dispatch')

    jobs = DispatchJob.objects.filter(organization=org).order_by('-scheduled_time')
    
    context = {
        'jobs': jobs,
        'vehicles': Vehicle.objects.filter(organization=org),
        'drivers': User.objects.filter(organization=org, role='DRIVER')
    }
    return render(request, 'fleet/dispatch.html', context)


# 14. Reports & Analytics
@login_required
def reports_view(request):
    org = get_user_org(request)
    vehicles = Vehicle.objects.filter(organization=org)
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="fleet_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Vehicle Code', 'Reg Number', 'Type', 'Mileage (km)', 'Engine Hours', 'Status', 'Health Score'])
        for v in vehicles:
            writer.writerow([v.vehicle_code, v.registration_number, v.vehicle_type, v.mileage_km, v.engine_hours, v.status, v.health_score_breakdown['score']])
        return response

    context = {
        'vehicles': vehicles,
        'total_trips': Trip.objects.filter(organization=org).count(),
        'total_fuel_cost': FuelLog.objects.filter(organization=org).aggregate(s=Sum('total_cost'))['s'] or 0.0,
        'total_maint_cost': MaintenanceRecord.objects.filter(organization=org).aggregate(s=Sum('total_cost'))['s'] or 0.0,
    }
    return render(request, 'fleet/reports.html', context)


# 15. AI Fleet Assistant
@login_required
def ai_assistant_view(request):
    org = get_user_org(request)
    return render(request, 'fleet/ai_assistant.html', {'org': org})


@csrf_exempt
@login_required
def api_ai_query(request):

    if request.method == 'POST':
        body = json.loads(request.body or '{}')
        query = body.get('query', '').lower()
        org = get_user_org(request)
        
        vehicles = Vehicle.objects.filter(organization=org)
        expenses = Expense.objects.filter(organization=org)
        maint = MaintenanceRecord.objects.filter(organization=org)
        fuel = FuelLog.objects.filter(organization=org)
        docs = Document.objects.filter(organization=org)
        
        if 'cost' in query or 'expense' in query:
            highest_exp_v = vehicles.annotate(exp_sum=Sum('expenses__amount')).order_by('-exp_sum').first()
            response_text = f"Based on telemetry logs, **{highest_exp_v.vehicle_code if highest_exp_v else 'N/A'}** has accumulated the highest operational expenses this month. Total fleet expense is **${expenses.aggregate(s=Sum('amount'))['s'] or 0:.2f}**."
        elif 'maintenance' in query or 'service' in query:
            due_count = maint.filter(status='SCHEDULED').count()
            response_text = f"There are currently **{due_count}** vehicles/machines scheduled for service. {vehicles.filter(status='MAINTENANCE').count()} vehicle(s) are currently inside the workshop."
        elif 'document' in query or 'expire' in query:
            exp_docs = [d for d in docs if d.status() in ['EXPIRED', 'EXPIRING_SOON']]
            response_text = f"You have **{len(exp_docs)}** document(s) that are expired or expiring within 30 days. Priority attention needed for vehicle permits and driver licenses."
        elif 'idle' in query or 'efficiency' in query:
            idle_v = vehicles.filter(status='IDLE').count()
            response_text = f"Currently **{idle_v}** out of {vehicles.count()} vehicles are idling. Reducing idle time by 15% can save approximately $450 in monthly fuel costs."
        else:
            response_text = f"Your fleet currently has **{vehicles.count()} active vehicles**, **{Trip.objects.filter(organization=org, status='IN_PROGRESS').count()} active trips**, and a fleet health score of **{int(sum([v.health_score_breakdown['score'] for v in vehicles])/max(1, vehicles.count()))}%**."

        return JsonResponse({'response': response_text})
    return JsonResponse({'error': 'POST required'}, status=400)


# 16. Centralized Alerts Center
@login_required
def alerts_view(request):
    org = get_user_org(request)
    alerts = Alert.objects.filter(organization=org).order_by('-created_at')
    
    context = {
        'alerts': alerts
    }
    return render(request, 'fleet/alerts.html', context)


# 17. Audit Log
@login_required
def audit_log_view(request):
    org = get_user_org(request)
    logs = AuditLog.objects.filter(organization=org).order_by('-timestamp')
    
    context = {
        'logs': logs
    }
    return render(request, 'fleet/audit_log.html', context)


# 18. Users & Role Management
@login_required
def users_roles_view(request):
    org = get_user_org(request)
    users = User.objects.filter(organization=org)
    
    context = {
        'users': users,
        'roles': User.ROLE_CHOICES
    }
    return render(request, 'fleet/users_roles.html', context)


# 19. Billing & SaaS Subscriptions
@login_required
def billing_view(request):
    org = get_user_org(request)
    sub, created = Subscription.objects.get_or_create(
        organization=org,
        defaults={'current_period_end': timezone.now().date() + timedelta(days=30)}
    )
    context = {
        'sub': sub,
        'org': org
    }
    return render(request, 'fleet/billing.html', context)


# 20. Settings
@login_required
def settings_view(request):
    org = get_user_org(request)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        country = request.POST.get('country_code')
        
        if name:
            org.name = name
            
        currency_map = {
            'IN': ('India', 'INR', '₹'),
            'US': ('United States', 'USD', '$'),
            'EU': ('Eurozone', 'EUR', '€'),
            'GB': ('United Kingdom', 'GBP', '£'),
            'AE': ('United Arab Emirates', 'AED', 'AED'),
            'SA': ('Saudi Arabia', 'SAR', 'SAR'),
            'CA': ('Canada', 'CAD', 'C$'),
            'AU': ('Australia', 'AUD', 'A$'),
            'JP': ('Japan', 'JPY', '¥'),
        }
        
        if country and country in currency_map:
            c_name, c_code, c_sym = currency_map[country]
            org.country_code = country
            org.country_name = c_name
            org.currency_code = c_code
            org.currency_symbol = c_sym
            
        org.save()
        messages.success(request, f"Organization preferences updated! Country set to {org.country_name} ({org.currency_symbol} {org.currency_code}).")
        return redirect(request.META.get('HTTP_REFERER', 'settings'))

    context = {
        'org': org,
        'countries': [
            {'code': 'IN', 'name': 'India 🇮🇳', 'currency': 'INR (₹)', 'symbol': '₹'},
            {'code': 'US', 'name': 'United States 🇺🇸', 'currency': 'USD ($)', 'symbol': '$'},
            {'code': 'EU', 'name': 'Eurozone 🇪🇺', 'currency': 'EUR (€)', 'symbol': '€'},
            {'code': 'GB', 'name': 'United Kingdom 🇬🇧', 'currency': 'GBP (£)', 'symbol': '£'},
            {'code': 'AE', 'name': 'United Arab Emirates 🇦🇪', 'currency': 'AED (AED)', 'symbol': 'AED'},
            {'code': 'SA', 'name': 'Saudi Arabia 🇸🇦', 'currency': 'SAR (SAR)', 'symbol': 'SAR'},
            {'code': 'CA', 'name': 'Canada 🇨🇦', 'currency': 'CAD (C$)', 'symbol': 'C$'},
            {'code': 'AU', 'name': 'Australia 🇦🇺', 'currency': 'AUD (A$)', 'symbol': 'A$'},
            {'code': 'JP', 'name': 'Japan 🇯🇵', 'currency': 'JPY (¥)', 'symbol': '¥'},
        ]
    }
    return render(request, 'fleet/settings.html', context)


    return render(request, 'fleet/settings.html', {'org': org})


# API Endpoint for Driver PWA Live GPS updates
@csrf_exempt
def api_log_gps(request):
    if request.method == 'POST':
        data = json.loads(request.body or '{}')
        driver_id = data.get('driver_id')
        lat = float(data.get('lat', 0.0))
        lng = float(data.get('lng', 0.0))
        speed = float(data.get('speed', 0.0))
        heading = float(data.get('heading', 0.0))
        accuracy = float(data.get('accuracy', 5.0))
        battery = int(data.get('battery', 90))
        
        driver = User.objects.filter(id=driver_id).first()
        if driver and driver.assigned_vehicles.exists():
            vehicle = driver.assigned_vehicles.first()
            vehicle.last_lat = lat
            vehicle.last_lng = lng
            vehicle.last_speed = speed
            vehicle.last_heading = heading
            vehicle.battery_level = battery
            vehicle.last_gps_update = timezone.now()
            vehicle.status = 'MOVING' if speed > 2 else ('IDLE' if speed == 0 else 'STOPPED')
            vehicle.save()

            active_trip = Trip.objects.filter(vehicle=vehicle, status='IN_PROGRESS').first()
            GPSLog.objects.create(
                vehicle=vehicle,
                trip=active_trip,
                lat=lat,
                lng=lng,
                speed=speed,
                heading=heading,
                accuracy=accuracy,
                battery_level=battery
            )
            return JsonResponse({'status': 'ok', 'vehicle_status': vehicle.status})
            
    return JsonResponse({'error': 'Invalid payload'}, status=400)
