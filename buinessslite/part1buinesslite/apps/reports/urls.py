from django.urls import path
from apps.reports import views

urlpatterns = [
    path('', views.reports_dashboard_view, name='reports_dashboard'),
    path('export/<str:report_type>/csv/', views.export_csv_view, name='export_csv'),
]
