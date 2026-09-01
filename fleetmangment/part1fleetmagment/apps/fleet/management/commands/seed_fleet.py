from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from apps.fleet.models import (
    Organization, User, Vehicle, Trip, GPSLog, Geofence, GeofenceLog,
    MaintenanceRecord, FuelLog, Expense, Document, InspectionChecklist,
    DispatchJob, Alert, AuditLog, Subscription
)

class Command(BaseCommand):
    help = 'Seeds initial realistic fleet telemetry and SaaS sample data for main and guest demo orgs.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting fleet data seeding..."))

        orgs_to_seed = [
            ('karobar-logistics', 'Karobar Logistics & Infrastructure Ltd'),
            ('public-demo-fleet', 'Public Demo Fleet Corp')
        ]

        for slug, name in orgs_to_seed:
            org, _ = Organization.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'max_vehicles': 100, 'max_users': 50, 'plan_name': 'ENTERPRISE'}
            )

            Subscription.objects.get_or_create(
                organization=org,
                defaults={
                    'plan_name': 'Enterprise Heavy Fleet',
                    'monthly_price': 299.00,
                    'status': 'ACTIVE',
                    'current_period_end': timezone.now().date() + timedelta(days=365)
                }
            )

            # Admin
            admin_user, created = User.objects.get_or_create(
                username='admin' if slug == 'karobar-logistics' else 'guest_demo',
                defaults={
                    'organization': org,
                    'role': 'OWNER' if slug == 'karobar-logistics' else 'VIEWER',
                    'email': f'admin@{slug}.com',
                    'first_name': 'Rajesh' if slug == 'karobar-logistics' else 'Guest',
                    'last_name': 'Sharma' if slug == 'karobar-logistics' else 'User',
                    'is_staff': (slug == 'karobar-logistics'),
                    'is_superuser': (slug == 'karobar-logistics')
                }
            )
            if created:
                admin_user.set_password('admin123' if slug == 'karobar-logistics' else 'guestdemo123!')
                admin_user.save()

            # Drivers
            d1, _ = User.objects.get_or_create(
                username=f'driver1_{slug[:4]}',
                defaults={
                    'organization': org,
                    'role': 'DRIVER',
                    'first_name': 'Vikram',
                    'last_name': 'Singh',
                    'phone': '+91 98765 43210',
                    'license_number': 'DL-2023-884920',
                    'license_expiry': timezone.now().date() + timedelta(days=400),
                    'employee_id': 'EMP-D01',
                    'driving_score': 94
                }
            )

            d2, _ = User.objects.get_or_create(
                username=f'driver2_{slug[:4]}',
                defaults={
                    'organization': org,
                    'role': 'DRIVER',
                    'first_name': 'Amit',
                    'last_name': 'Kumar',
                    'phone': '+91 98123 76543',
                    'license_number': 'DL-2022-110293',
                    'license_expiry': timezone.now().date() + timedelta(days=15),
                    'employee_id': 'EMP-D02',
                    'driving_score': 78
                }
            )

            # Vehicles
            v_data = [
                {'code': 'TR-101', 'reg': 'DL-01-AB-1234', 'type': 'TRUCK', 'brand': 'Volvo', 'model': 'FH16 750', 'km': 48500, 'hrs': 1200, 'status': 'MOVING', 'lat': 28.6139, 'lng': 77.2090, 'speed': 62.0, 'driver': d1},
                {'code': 'JCB-201', 'reg': 'HR-26-CV-5678', 'type': 'JCB', 'brand': 'JCB', 'model': '3DX Super', 'km': 12400, 'hrs': 3450, 'status': 'IDLE', 'lat': 28.4595, 'lng': 77.0266, 'speed': 0.0, 'driver': d2},
                {'code': 'CAT-301', 'reg': 'UP-16-EX-9900', 'type': 'EXCAVATOR', 'brand': 'Caterpillar', 'model': '320 GX', 'km': 8900, 'hrs': 4890, 'status': 'MAINTENANCE', 'lat': 28.5355, 'lng': 77.3910, 'speed': 0.0, 'driver': None},
                {'code': 'VAN-401', 'reg': 'DL-03-CC-4455', 'type': 'VAN', 'brand': 'Tata', 'model': 'Winger Cargo', 'km': 31200, 'hrs': 850, 'status': 'MOVING', 'lat': 28.7041, 'lng': 77.1025, 'speed': 45.0, 'driver': d1},
                {'code': 'GEN-501', 'reg': 'GEN-HUB-01', 'type': 'GENERATOR', 'brand': 'Cummins', 'model': '500 kVA', 'km': 0, 'hrs': 5600, 'status': 'STOPPED', 'lat': 28.6280, 'lng': 77.3750, 'speed': 0.0, 'driver': None},
            ]

            vehicles_list = []
            for item in v_data:
                v, _ = Vehicle.objects.get_or_create(
                    organization=org,
                    vehicle_code=item['code'],
                    defaults={
                        'registration_number': item['reg'],
                        'vehicle_type': item['type'],
                        'brand': item['brand'],
                        'model': item['model'],
                        'year': 2024,
                        'fuel_type': 'DIESEL',
                        'mileage_km': item['km'],
                        'engine_hours': item['hrs'],
                        'status': item['status'],
                        'last_lat': item['lat'],
                        'last_lng': item['lng'],
                        'last_speed': item['speed'],
                        'current_driver': item['driver'],
                        'last_gps_update': timezone.now()
                    }
                )
                vehicles_list.append(v)

            # Trips
            t1, _ = Trip.objects.get_or_create(
                organization=org,
                trip_id=f'TRIP-{slug[:4]}-001',
                defaults={
                    'vehicle': vehicles_list[0],
                    'driver': d1,
                    'start_location': 'Delhi Inland Container Depot',
                    'destination': 'Gurugram Logistics Park Hub 4',
                    'start_time': timezone.now() - timedelta(hours=2),
                    'distance_km': 48.5,
                    'duration_minutes': 95,
                    'avg_speed_kmh': 42.0,
                    'max_speed_kmh': 74.0,
                    'idle_minutes': 12,
                    'status': 'IN_PROGRESS'
                }
            )


            # GPS Telemetry
            base_lat, base_lng = 28.6139, 77.2090
            for i in range(15):
                GPSLog.objects.create(
                    vehicle=vehicles_list[0],
                    trip=t1,
                    lat=base_lat + (i * 0.005),
                    lng=base_lng + (i * 0.008),
                    speed=40.0 + random.randint(-5, 20),
                    heading=120.0,
                    accuracy=3.5,
                    battery_level=98,
                    recorded_at=timezone.now() - timedelta(minutes=(15-i)*5)
                )

            # Geofences
            g1, _ = Geofence.objects.get_or_create(
                organization=org,
                name='Gurugram Hub 4 Warehouse',
                defaults={'category': 'WAREHOUSE', 'geofence_type': 'CIRCLE', 'center_lat': 28.4595, 'center_lng': 77.0266, 'radius_meters': 500}
            )

            GeofenceLog.objects.get_or_create(
                organization=org,
                geofence=g1,
                vehicle=vehicles_list[0],
                event_type='ENTER',
                defaults={'timestamp': timezone.now() - timedelta(minutes=45)}
            )

            # Maintenance Records
            MaintenanceRecord.objects.get_or_create(
                organization=org,
                vehicle=vehicles_list[2],
                title='Hydraulic Cylinder Leak & Oil Filter Service',
                defaults={
                    'maintenance_type': 'REPAIR',
                    'workshop_name': 'Caterpillar Authorized Service Center',
                    'parts_cost': 240.00,
                    'labor_cost': 120.00,
                    'total_cost': 360.00,
                    'status': 'IN_PROGRESS',
                    'service_date': timezone.now().date()
                }
            )

            # Fuel Logs
            if not FuelLog.objects.filter(organization=org, vehicle=vehicles_list[0]).exists():
                FuelLog.objects.create(
                    organization=org,
                    vehicle=vehicles_list[0],
                    driver=d1,
                    fuel_quantity_liters=140.0,
                    price_per_liter=1.15,
                    total_cost=161.00,
                    odometer_km=48200.0,
                    fuel_station='IndianOil Highway Hub Station 14',
                    date=timezone.now().date(),
                    is_suspicious=False
                )

            # Expenses
            if not Expense.objects.filter(organization=org, vehicle=vehicles_list[0]).exists():
                Expense.objects.create(
                    organization=org,
                    vehicle=vehicles_list[0],
                    category='TOLL',
                    amount=45.00,
                    notes='Expressway FastTag Plaza Crossing',
                    date=timezone.now().date()
                )

            # Documents
            if not Document.objects.filter(organization=org, title='Heavy Equipment Pollution Certificate (PUC)').exists():
                Document.objects.create(
                    organization=org,
                    title='Heavy Equipment Pollution Certificate (PUC)',
                    vehicle=vehicles_list[2],
                    doc_type='POLLUTION',
                    expiry_date=timezone.now().date() + timedelta(days=5)
                )


            # Dispatch Jobs
            if not DispatchJob.objects.filter(organization=org, job_code=f'JOB-{slug[:4]}-101').exists():
                DispatchJob.objects.create(
                    organization=org,
                    job_code=f'JOB-{slug[:4]}-101',
                    title='Heavy Machinery Site Transfer',
                    driver=d2,
                    vehicle=vehicles_list[1],
                    destination_address='Noida Sector 62 Construction Project',
                    scheduled_time=timezone.now() + timedelta(hours=4),
                    status='ASSIGNED',
                    instructions='Verify hydraulic pressure before site dispatch.'
                )

            # Alerts
            if not Alert.objects.filter(organization=org, title='Document Expiry Warning').exists():
                Alert.objects.create(
                    organization=org,
                    title='Document Expiry Warning',
                    vehicle=vehicles_list[2],
                    alert_type='DOCUMENT_EXPIRY',
                    severity='HIGH',
                    message='CAT-301 Pollution Certificate expires in 5 days.'
                )


            # Audit Logs
            AuditLog.objects.get_or_create(
                organization=org,
                action=f'Database initialized with telemetry for {slug}',
                defaults={'user': admin_user, 'ip_address': '127.0.0.1'}
            )

        self.stdout.write(self.style.SUCCESS("Fleet data seeding completed successfully!"))
