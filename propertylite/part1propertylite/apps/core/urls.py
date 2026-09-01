from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('login/', views.login_view, name='login'),
    path('guest-login/', views.guest_login_view, name='guest_login'),
    path('guest-upgrade/', views.guest_upgrade_view, name='guest_upgrade'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/search/', views.global_search, name='global_search'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('notifications/', views.notifications_list, name='notifications'),
]
