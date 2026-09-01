from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('properties/', include('apps.properties.urls')),
    path('tenants/', include('apps.tenants.urls')),
    path('leases/', include('apps.leases.urls')),
    path('finance/', include('apps.finance.urls')),
    path('maintenance/', include('apps.maintenance.urls')),
    path('portal/', include('apps.portal.urls')),
    path('ai/', include('apps.ai_assistant.urls')),
    path('reports/', include('apps.reports.urls')),
    path('billing/', include('apps.billing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
