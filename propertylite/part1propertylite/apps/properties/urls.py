from django.urls import path
from . import views

urlpatterns = [
    path('', views.property_list, name='property_list'),
    path('new/', views.property_create, name='property_create'),
    path('<int:pk>/', views.property_detail, name='property_detail'),
    path('<int:property_pk>/units/new/', views.unit_create, name='unit_create'),
]
