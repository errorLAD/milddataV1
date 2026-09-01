from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import date, timedelta

from apps.tenants.models import Organization, UserProfile
from apps.machines.models import Machine, MeterLog, MachineLocation, GeofenceZone
from apps.operators.models import Operator
from apps.projects.models import Project, MachineAllocation
from apps.fuel.models import FuelLog
from apps.maintenance.models import MaintenanceLog
from apps.documents.models import MachineDocument
from apps.finance.models import RevenueLog, ExpenseLog
from apps.notifications.models import Notification
from apps.billing.models import Subscription
from apps.trips.models import Trip
from apps.inventory.models import SparePart, PartTransaction
from apps.rentals.models import RentalCustomer, RentalContract

class Command(BaseCommand):
    help = 'Seeds database with comprehensive enterprise heavy equipment data including GPS location telemetry and geofences'

    def handle(self, *args, **options):
        self.stdout.write("Seeding complete Machine OS fleet dataset with GPS telemetry...")

        # 1. Organization Tenant
        org, _ = Organization.objects.get_or_create(
            code='KEL-001',
            defaults={
                'name': 'Karobar Equipment Logistics Pvt Ltd',
                'currency_symbol': '₹',
                'currency_code': 'INR'
            }
        )

        # 2. Superuser & Admin Profile
        user, created = User.objects.get_or_create(username='admin')
        if created:
            user.set_password('admin123')
            user.is_staff = True
            user.is_superuser = True
            user.save()

        UserProfile.objects.get_or_create(
            user=user,
            defaults={'organization': org, 'role': 'admin', 'phone': '+91 98765 43210'}
        )

        # 3. Comprehensive Machine Fleet (10 Equipment Units)
        fleet_data = [
            ('JCB 3DX Super #101', 'KA-04-MB-8921', 'jcb', 'JCB 3DX Super 4WD', 2022, 'hours', 3450.5, 'working', 1200.0, 9500.0, 3400000.0, 12.9716, 77.5946, 'NH-48 Expressway Site, Bengaluru', 18.5, True),
            ('CAT 320 Excavator #04', 'KA-05-EX-4412', 'excavator', 'Caterpillar 320D NextGen', 2023, 'hours', 1820.0, 'working', 2100.0, 16500.0, 7200000.0, 13.0827, 77.5877, 'Metro Rail Line 3 Corridor', 0.0, True),
            ('Tata Prima 2830 Dumper #08', 'MH-12-PQ-9011', 'dumper', 'Tata Prima 2830.TK Tipper', 2021, 'km', 42100.0, 'working', 900.0, 8000.0, 4800000.0, 12.9250, 77.6200, 'Koramangala Construction Zone', 32.0, True),
            ('LIEBHERR LTM Crane 50T', 'DL-01-CR-2200', 'crane', 'Liebherr LTM 1050 Mobile Crane', 2020, 'hours', 890.0, 'idle', 3500.0, 28000.0, 14500000.0, 12.9900, 77.5700, 'Central Logistics Yard', 0.0, False),
            ('Mahindra 575 Tractor #12', 'HR-26-TR-7721', 'tractor', 'Mahindra 575 DI SP Plus', 2019, 'hours', 1410.0, 'breakdown', 600.0, 4500.0, 850000.0, 13.0100, 77.6500, 'Whitefield Site Yard', 0.0, False),
            ('VOLVO EC210D Excavator #09', 'TN-09-EX-9988', 'excavator', 'Volvo EC210D Prime', 2023, 'hours', 2150.0, 'working', 2300.0, 18000.0, 7800000.0, 12.9500, 77.5300, 'City Center Mall Excavation', 5.0, True),
            ('Cummins 125kVA Generator #02', 'GEN-125-02', 'generator', 'Cummins Silent DG Set 125kVA', 2022, 'hours', 2890.0, 'working', 500.0, 3500.0, 1100000.0, 13.0827, 77.5877, 'Metro Rail Line 3 Corridor', 0.0, True),
            ('Ashok Leyland 2820 Dumper #14', 'KA-04-DP-3321', 'dumper', 'Ashok Leyland 2820 Tipper', 2022, 'km', 31200.0, 'working', 850.0, 7500.0, 4200000.0, 12.9716, 77.5946, 'NH-48 Expressway Site', 24.5, True),
            ('JCB 4DX Wheel Loader #03', 'GJ-01-WL-5544', 'loader', 'JCB 4DX Heavy Loader', 2021, 'hours', 3910.0, 'maintenance', 1500.0, 12000.0, 4100000.0, 12.9900, 77.5700, 'JCB Authorized Workshop', 0.0, False),
            ('Atlas Copco Air Compressor #01', 'COMP-400-01', 'other', 'Atlas Copco XAS 400', 2020, 'hours', 1950.0, 'idle', 400.0, 2800.0, 950000.0, 12.9900, 77.5700, 'Central Logistics Yard', 0.0, False),
        ]

        created_machines = []
        for name, reg, cat, model, year, trk, meter, st, hr_rt, dy_rt, val, lat, lng, loc_name, spd, ign in fleet_data:
            m, _ = Machine.objects.get_or_create(
                organization=org, reg_number=reg,
                defaults={
                    'name': name, 'category': cat, 'make_model': model,
                    'model_year': year, 'tracking_type': trk, 'current_meter': meter,
                    'status': st, 'hourly_rate': hr_rt, 'daily_rate': dy_rt,
                    'estimated_value': val
                }
            )
            created_machines.append(m)

            # Machine Location
            MachineLocation.objects.update_or_create(
                machine=m,
                defaults={
                    'latitude': lat,
                    'longitude': lng,
                    'location_name': loc_name,
                    'speed_kmh': spd,
                    'ignition_on': ign
                }
            )

        # 4. Geofence Zones
        GeofenceZone.objects.get_or_create(
            organization=org, name='NH-48 Expressway Construction Zone',
            defaults={'center_lat': 12.9716, 'center_lng': 77.5946, 'radius_km': 5.0}
        )
        GeofenceZone.objects.get_or_create(
            organization=org, name='Metro Rail Corridor Boundary',
            defaults={'center_lat': 13.0827, 'center_lng': 77.5877, 'radius_km': 3.5}
        )

        # 5. Operators Roster
        op1, _ = Operator.objects.get_or_create(
            organization=org, name='Ramesh Kumar',
            defaults={'phone': '9811223344', 'license_number': 'DL-KA04-2018-991', 'assigned_machine': created_machines[0], 'daily_salary': 900.00, 'performance_score': 95}
        )
        op2, _ = Operator.objects.get_or_create(
            organization=org, name='Suresh Patil',
            defaults={'phone': '9822334455', 'license_number': 'DL-KA05-2020-412', 'assigned_machine': created_machines[1], 'daily_salary': 1200.00, 'performance_score': 92}
        )

        # 6. Trips & Dispatch
        Trip.objects.get_or_create(
            organization=org, trip_number='TRIP-1091',
            defaults={
                'machine': created_machines[0], 'driver': op1,
                'pickup_location': 'Central Equipment Yard', 'drop_location': 'NH-48 Expressway Site',
                'distance_km': 45.0, 'status': 'completed', 'expenses': 1200.00,
                'proof_of_work': 'Completed 8 hours excavation at site.'
            }
        )

        # 7. Spare Parts & Inventory
        sp1, _ = SparePart.objects.get_or_create(
            organization=org, sku='PRT-JCB-902',
            defaults={'name': 'Hydraulic Seal Kit JCB 3DX', 'category': 'Hydraulics', 'stock_quantity': 8, 'min_stock_threshold': 3, 'unit_cost': 2400.00, 'supplier_name': 'JCB Genuine Spares'}
        )

        # 8. Rental Customer & Contract
        cust, _ = RentalCustomer.objects.get_or_create(
            organization=org, name='L&T Heavy Civil Infra',
            defaults={'phone': '9800112233', 'email': 'procurement@ltinfra.com', 'tax_id': '29AAAAA0000A1Z5'}
        )
        RentalContract.objects.get_or_create(
            organization=org, contract_number='RC-2026-004',
            defaults={
                'customer': cust, 'machine': created_machines[1],
                'start_date': date.today() - timedelta(days=15),
                'agreed_rate': 16500.00, 'deposit_amount': 50000.00,
                'handover_meter': 1600.0, 'status': 'active',
                'handover_condition': 'Passed 15-point mechanical inspection.'
            }
        )

        # 9. Maintenance Logs
        MaintenanceLog.objects.get_or_create(
            organization=org, machine=created_machines[0], date=date.today() - timedelta(days=15),
            defaults={'service_type': 'preventive', 'meter_reading': 3400.0, 'cost': 14500.00, 'vendor_mechanic': 'JCB Authorized Workshop', 'parts_replaced': 'Engine oil 15W40, Oil Filter, Air Filter', 'next_service_meter': 3650.0}
        )

        self.stdout.write(self.style.SUCCESS("Complete Machine OS dataset (GPS Telemetry, Maps, Geofences) populated!"))
