from django.urls import path
from . import views

urlpatterns = [
    path('', views.maintenance_list, name='maintenance_list'),
    path('add/', views.add_maintenance, name='add_maintenance'),
]
