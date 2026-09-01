from django.urls import path
from apps.finance import views

urlpatterns = [
    path('receivables/', views.receivables_view, name='receivables'),
    path('payables/', views.payables_view, name='payables'),
    path('payment/record/', views.record_payment_view, name='record_payment'),
    path('profitability/', views.profitability_view, name='profitability'),
]
