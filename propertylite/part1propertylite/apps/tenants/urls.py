from django.urls import path
from . import views

urlpatterns = [
    path('', views.tenant_list, name='tenant_list'),
    path('new/', views.tenant_create, name='tenant_create'),
    path('<int:pk>/', views.tenant_detail, name='tenant_detail'),
]
