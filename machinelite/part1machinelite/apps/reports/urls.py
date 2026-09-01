from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_overview, name='reports_overview'),
    path('export/csv/', views.export_fleet_csv, name='export_fleet_csv'),
]
