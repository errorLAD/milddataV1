from django.urls import path
from . import views

urlpatterns = [
    path('', views.lease_list, name='lease_list'),
    path('new/', views.lease_create, name='lease_create'),
    path('<int:pk>/', views.lease_detail, name='lease_detail'),
]
