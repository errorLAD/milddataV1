from django.urls import path
from apps.importer import views

urlpatterns = [
    path('', views.import_csv_view, name='import_csv'),
    path('template/', views.download_template_csv, name='download_template_csv'),
]
