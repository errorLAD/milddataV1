from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('add/', views.add_spare_part, name='add_spare_part'),
    path('transaction/', views.stock_transaction, name='stock_transaction'),
]
