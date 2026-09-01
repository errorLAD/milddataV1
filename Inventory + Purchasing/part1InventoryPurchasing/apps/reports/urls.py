from django.urls import path
from apps.reports import views

urlpatterns = [
    path('', views.reports_index_view, name='reports_index'),
    path('export/', views.export_report_csv, name='export_report_csv'),
]
