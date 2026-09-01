from django.urls import path
from apps.finance import views

urlpatterns = [
    path('expenses/', views.expense_list_view, name='expense_list'),
    path('expenses/create/', views.expense_create_view, name='expense_create'),
    path('receivables/', views.receivables_view, name='receivables'),
    path('payables/', views.payables_view, name='payables'),
    path('profit/', views.profit_view, name='profit'),
]
