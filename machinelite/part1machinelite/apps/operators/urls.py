from django.urls import path
from . import views

urlpatterns = [
    path('', views.operator_list, name='operator_list'),
    path('add/', views.add_operator, name='add_operator'),
]
