from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.fleet import views as fleet_views
from apps.pwa import views as pwa_views
from apps.superadmin import views as superadmin_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth
    path('login/', fleet_views.login_view, name='login'),
    path('guest-login/', fleet_views.guest_login_view, name='guest_login'),
    path('logout/', fleet_views.logout_view, name='logout'),

    
    # Admin / Owner Web Dashboard & Modules
    path('', fleet_views.dashboard_view, name='dashboard'),
    path('tracking/', fleet_views.tracking_view, name='tracking'),
    
    path('trips/', fleet_views.trips_list_view, name='trips_list'),
    path('trips/<int:trip_id>/', fleet_views.trip_detail_view, name='trip_detail'),
    path('trips/playback/', fleet_views.route_playback_view, name='route_playback'),
    
    path('geofences/', fleet_views.geofences_view, name='geofences'),
    
    path('vehicles/', fleet_views.vehicles_list_view, name='vehicles_list'),
    path('vehicles/<int:pk>/', fleet_views.vehicle_detail_view, name='vehicle_detail'),
    
    path('drivers/', fleet_views.drivers_list_view, name='drivers_list'),
    path('maintenance/', fleet_views.maintenance_view, name='maintenance'),
    path('fuel/', fleet_views.fuel_view, name='fuel'),
    path('expenses/', fleet_views.expenses_view, name='expenses'),
    path('documents/', fleet_views.documents_view, name='documents'),
    path('inspections/', fleet_views.inspections_view, name='inspections'),
    path('dispatch/', fleet_views.dispatch_view, name='dispatch'),
    path('reports/', fleet_views.reports_view, name='reports'),
    path('ai-assistant/', fleet_views.ai_assistant_view, name='ai_assistant'),
    path('alerts/', fleet_views.alerts_view, name='alerts'),
    path('audit-log/', fleet_views.audit_log_view, name='audit_log'),
    path('users-roles/', fleet_views.users_roles_view, name='users_roles'),
    path('billing/', fleet_views.billing_view, name='billing'),
    path('settings/', fleet_views.settings_view, name='settings'),
    
    # API endpoints
    path('api/v1/gps/log/', fleet_views.api_log_gps, name='api_log_gps'),
    path('api/v1/ai/query/', fleet_views.api_ai_query, name='api_ai_query'),
    
    # Driver PWA
    path('pwa/', pwa_views.pwa_home, name='pwa_home'),
    path('pwa/trip/', pwa_views.pwa_trip, name='pwa_trip'),
    path('pwa/jobs/', pwa_views.pwa_jobs, name='pwa_jobs'),
    path('pwa/inspection/', pwa_views.pwa_inspection, name='pwa_inspection'),
    path('pwa/history/', pwa_views.pwa_history, name='pwa_history'),
    path('pwa/vehicle/', pwa_views.pwa_vehicle, name='pwa_vehicle'),
    path('pwa/profile/', pwa_views.pwa_profile, name='pwa_profile'),
    
    path('manifest.webmanifest', pwa_views.manifest_view, name='pwa_manifest'),
    path('sw.js', pwa_views.service_worker_view, name='pwa_sw'),

    # Super Admin SaaS Panel
    path('superadmin/', superadmin_views.superadmin_dashboard, name='superadmin_dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
