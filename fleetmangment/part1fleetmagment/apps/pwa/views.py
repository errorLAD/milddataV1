from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from apps.fleet.models import (
    Vehicle, Trip, DispatchJob, InspectionChecklist, User, GPSLog, AuditLog
)
import json

@login_required
def pwa_home(request):
    driver = request.user
    assigned_vehicle = driver.assigned_vehicles.first()
    active_trip = Trip.objects.filter(driver=driver, status__in=['STARTED', 'IN_PROGRESS', 'PAUSED']).first()
    pending_jobs = DispatchJob.objects.filter(driver=driver, status__in=['ASSIGNED', 'ACCEPTED', 'IN_TRANSIT']).count()

    context = {
        'driver': driver,
        'assigned_vehicle': assigned_vehicle,
        'active_trip': active_trip,
        'pending_jobs': pending_jobs,
    }
    return render(request, 'pwa/home.html', context)


@login_required
def pwa_trip(request):
    driver = request.user
    assigned_vehicle = driver.assigned_vehicles.first()
    active_trip = Trip.objects.filter(driver=driver, status__in=['STARTED', 'IN_PROGRESS', 'PAUSED']).first()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'start':
            if not active_trip and assigned_vehicle:
                trip_code = f"TRIP-{timezone.now().strftime('%m%d%H%M%S')}"
                active_trip = Trip.objects.create(
                    organization=driver.organization,
                    trip_id=trip_code,
                    driver=driver,
                    vehicle=assigned_vehicle,
                    start_time=timezone.now(),
                    status='IN_PROGRESS',
                    start_location="Driver PWA Departure Site"
                )
                assigned_vehicle.status = 'MOVING'
                assigned_vehicle.save()
                AuditLog.objects.create(
                    organization=driver.organization,
                    user=driver,
                    action=f"Driver started Trip {trip_code}"
                )
                return redirect('pwa_trip')

        elif action == 'pause' and active_trip:
            active_trip.status = 'PAUSED'
            active_trip.save()
            return redirect('pwa_trip')

        elif action == 'resume' and active_trip:
            active_trip.status = 'IN_PROGRESS'
            active_trip.save()
            return redirect('pwa_trip')

        elif action == 'stop' and active_trip:
            active_trip.status = 'COMPLETED'
            active_trip.end_time = timezone.now()
            active_trip.save()
            
            if assigned_vehicle:
                assigned_vehicle.status = 'STOPPED'
                assigned_vehicle.save()
                
            AuditLog.objects.create(
                organization=driver.organization,
                user=driver,
                action=f"Driver completed Trip {active_trip.trip_id}"
            )
            return redirect('pwa_home')

    context = {
        'assigned_vehicle': assigned_vehicle,
        'active_trip': active_trip,
    }
    return render(request, 'pwa/trip.html', context)


@login_required
def pwa_jobs(request):
    driver = request.user
    jobs = DispatchJob.objects.filter(driver=driver).order_by('-scheduled_time')
    
    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        new_status = request.POST.get('status')
        job = get_object_or_404(DispatchJob, id=job_id, driver=driver)
        job.status = new_status
        if new_status == 'DELIVERED':
            job.completed_at = timezone.now()
            job.customer_signature = request.POST.get('signature_data', '')
        job.save()
        return redirect('pwa_jobs')

    context = {
        'jobs': jobs
    }
    return render(request, 'pwa/jobs.html', context)


@login_required
def pwa_inspection(request):
    driver = request.user
    assigned_vehicle = driver.assigned_vehicles.first()
    
    if request.method == 'POST':
        tyres = request.POST.get('tyres') == 'on'
        brakes = request.POST.get('brakes') == 'on'
        lights = request.POST.get('lights') == 'on'
        engine = request.POST.get('engine') == 'on'
        battery = request.POST.get('battery') == 'on'
        fuel = request.POST.get('fuel') == 'on'
        notes = request.POST.get('notes', '')
        
        overall = 'PASS' if (tyres and brakes and lights and engine and battery and fuel) else 'FAIL'
        
        if assigned_vehicle:
            InspectionChecklist.objects.create(
                organization=driver.organization,
                vehicle=assigned_vehicle,
                driver=driver,
                tyres_passed=tyres,
                brakes_passed=brakes,
                lights_passed=lights,
                engine_passed=engine,
                battery_passed=battery,
                fuel_passed=fuel,
                overall_status=overall,
                notes=notes,
                signature_data=request.POST.get('signature_data', '')
            )
            return redirect('pwa_home')

    context = {
        'assigned_vehicle': assigned_vehicle
    }
    return render(request, 'pwa/inspection.html', context)


@login_required
def pwa_history(request):
    driver = request.user
    trips = Trip.objects.filter(driver=driver, status='COMPLETED').order_by('-end_time')
    return render(request, 'pwa/history.html', {'trips': trips})


@login_required
def pwa_vehicle(request):
    driver = request.user
    assigned_vehicle = driver.assigned_vehicles.first()
    return render(request, 'pwa/vehicle.html', {'vehicle': assigned_vehicle})


@login_required
def pwa_profile(request):
    return render(request, 'pwa/profile.html', {'driver': request.user})


# PWA Manifest and Service Worker handlers
def manifest_view(request):
    manifest_data = {
        "name": "Fleet Operating System - Driver PWA",
        "short_name": "Fleet Driver",
        "start_url": "/pwa/",
        "display": "standalone",
        "background_color": "#FFFFFF",
        "theme_color": "#2451FF",
        "icons": [
            {
                "src": "/static/images/pwa-icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/images/pwa-icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return JsonResponse(manifest_data)


def service_worker_view(request):
    sw_code = """
const CACHE_NAME = 'fleet-driver-pwa-v1';
const ASSETS = [
    '/pwa/',
    '/static/css/karobarplus.css',
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
    );
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        fetch(e.request).catch(() => caches.match(e.request))
    );
});
"""
    return HttpResponse(sw_code, content_type='application/javascript')
