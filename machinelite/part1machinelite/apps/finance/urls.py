from django.urls import path
from . import views

urlpatterns = [
    path('profit-loss/', views.profit_loss_view, name='profit_loss'),
    path('revenue/add/', views.add_revenue, name='add_revenue'),
    path('expense/add/', views.add_expense, name='add_expense'),
]
