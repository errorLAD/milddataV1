from django.contrib import admin
from django.urls import path, include
from apps.tenants import views as tenant_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', tenant_views.dashboard_view, name='dashboard'),
    path('login/', tenant_views.login_view, name='login'),
    path('guest-login/', tenant_views.guest_login_view, name='guest_login'),
    path('upgrade/', tenant_views.upgrade_account_view, name='upgrade_account'),
    path('logout/', tenant_views.logout_view, name='logout'),
    
    path('machines/', include('apps.machines.urls')),
    path('operators/', include('apps.operators.urls')),
    path('fuel/', include('apps.fuel.urls')),
    path('maintenance/', include('apps.maintenance.urls')),
    path('documents/', include('apps.documents.urls')),
    path('finance/', include('apps.finance.urls')),
    path('ai-assistant/', include('apps.ai_assistant.urls')),
    
    # Enterprise Production Modules
    path('notifications/', include('apps.notifications.urls')),
    path('search/', include('apps.search.urls')),
    path('reports/', include('apps.reports.urls')),
    path('import-export/', include('apps.import_export.urls')),
    path('billing/', include('apps.billing.urls')),
    path('settings/', include('apps.settings.urls')),
    path('support/', include('apps.support.urls')),
    path('admin-portal/', include('apps.admin_portal.urls')),
    
    # Operations & Dispatch Modules
    path('trips/', include('apps.trips.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('rentals/', include('apps.rentals.urls')),
]
