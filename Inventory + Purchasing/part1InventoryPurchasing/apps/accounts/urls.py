from django.urls import path
from apps.accounts import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('guest-login/', views.guest_login_view, name='guest_login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('settings/', views.settings_view, name='settings'),
]
