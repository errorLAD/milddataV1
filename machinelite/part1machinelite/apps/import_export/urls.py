from django.urls import path
from . import views

urlpatterns = [
    path('', views.import_view, name='import_index'),
    path('machines/', views.import_csv_machines, name='import_csv_machines'),
]
