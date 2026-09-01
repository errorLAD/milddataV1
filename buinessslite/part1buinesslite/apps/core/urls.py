from django.urls import path
from apps.core import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('guest-login/', views.guest_login_view, name='guest_login'),
    path('logout/', views.logout_view, name='logout'),
    path('settings/', views.settings_view, name='settings'),
    path('audit-log/', views.audit_log_view, name='audit_log'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('api/notifications/<int:notif_id>/read/', views.mark_notification_read_api, name='mark_notification_read_api'),
    path('api/quick-switch-country/', views.quick_switch_country_api, name='quick_switch_country_api'),
    path('api/ai-assistant/', views.ai_assistant_api, name='ai_assistant_api'),
    path('api/global-search/', views.global_search_api, name='global_search_api'),
    path('manifest.json', views.pwa_manifest_view, name='pwa_manifest'),
    path('sw.js', views.pwa_sw_view, name='pwa_sw'),
]
