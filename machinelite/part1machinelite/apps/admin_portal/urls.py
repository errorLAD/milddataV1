from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_portal_dashboard, name='admin_portal_dashboard'),
]
