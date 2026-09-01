from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_index, name='reports_index'),
    path('export/<str:report_type>/', views.export_csv, name='export_csv'),
]
