from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect, render
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from dashboard.views import LandingPageView

def root_redirect(request):
    if request.user.is_authenticated or getattr(request, 'is_guest', False):
        if hasattr(request.user, 'is_superuser') and (request.user.is_superuser or request.user.is_staff):
            return redirect('platform_admin:dashboard')
        return redirect('dashboard:index')
    return LandingPageView.as_view()(request)

urlpatterns = [
    path('', root_redirect, name='root'),
    path('landing/', LandingPageView.as_view(), name='landing'),
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('customers/', include('customers.urls', namespace='customers')),
    path('sales/', include('sales.urls', namespace='sales')),
    path('udhaar/', include('udhaar.urls', namespace='udhaar')),
    path('suppliers/', include('suppliers.urls', namespace='suppliers')),
    path('products/', include('products.urls', namespace='products')),
    path('ai-advisor/', include('ai_advisor.urls', namespace='ai_advisor')),
    path('whatsapp/', include('whatsapp.urls', namespace='whatsapp')),
    path('promotions/', include('promotions.urls', namespace='promotions')),
    path('sales-agent/', include('sales_agent.urls', namespace='sales_agent')),
    path('platform-admin/', include('platform_admin.urls', namespace='platform_admin')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('settings/', include('settings_app.urls', namespace='settings_app')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('collections/', include('b2bcollections.urls', namespace='collections')),
]

handler403 = lambda request, exception=None: render(request, '403.html', status=403)
handler404 = lambda request, exception=None: render(request, '404.html', status=404)
handler500 = lambda request: render(request, '500.html', status=500)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

