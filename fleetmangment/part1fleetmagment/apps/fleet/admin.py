from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Organization, User, Vehicle, Trip, GPSLog, Geofence, GeofenceLog,
    MaintenanceRecord, FuelLog, Expense, Document, InspectionChecklist,
    DispatchJob, Alert, AuditLog, Subscription
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Fleet SaaS Roles & Details', {'fields': ('organization', 'role', 'phone', 'photo', 'license_number', 'license_expiry', 'employee_id', 'driving_score', 'is_driver_available')}),
    )

admin.site.register(Organization)
admin.site.register(Vehicle)
admin.site.register(Trip)
admin.site.register(GPSLog)
admin.site.register(Geofence)
admin.site.register(GeofenceLog)
admin.site.register(MaintenanceRecord)
admin.site.register(FuelLog)
admin.site.register(Expense)
admin.site.register(Document)
admin.site.register(InspectionChecklist)
admin.site.register(DispatchJob)
admin.site.register(Alert)
admin.site.register(AuditLog)
admin.site.register(Subscription)
