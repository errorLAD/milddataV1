from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('people/', include('apps.people.urls')),
    path('sales/', include('apps.sales.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('purchasing/', include('apps.purchasing.urls')),
    path('finance/', include('apps.finance.urls')),
    path('operations/', include('apps.operations.urls')),
    path('reports/', include('apps.reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
