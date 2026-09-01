from django.urls import path
from . import views

urlpatterns = [
    path('', views.machine_list, name='machine_list'),
    path('add/', views.add_machine, name='add_machine'),
    path('map/', views.fleet_map_view, name='fleet_map'),
    path('health-matrix/', views.health_matrix_view, name='machine_health_matrix'),
    path('<int:pk>/', views.machine_detail, name='machine_detail'),
    path('<int:pk>/log-meter/', views.log_meter, name='log_meter'),
    path('<int:pk>/update-location/', views.update_location, name='update_location'),
]
