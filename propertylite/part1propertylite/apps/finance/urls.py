from django.urls import path
from . import views

urlpatterns = [
    path('rent/', views.rent_collection, name='rent_collection'),
    path('invoices/<int:invoice_pk>/pay/', views.payment_record, name='payment_record'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/new/', views.expense_create, name='expense_create'),
]
