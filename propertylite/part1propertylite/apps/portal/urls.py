from django.urls import path
from . import views

urlpatterns = [
    path('tenant/', views.tenant_pwa, name='tenant_pwa'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
]
