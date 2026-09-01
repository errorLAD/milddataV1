from django.urls import path
from apps.sales import views

urlpatterns = [
    path('customers/', views.customer_list_view, name='customer_list'),
    path('customers/create/', views.customer_create_view, name='customer_create'),
    path('customers/<int:customer_id>/', views.customer_detail_view, name='customer_detail'),

    path('quotes/', views.quote_list_view, name='quote_list'),
    path('quotes/create/', views.quote_create_view, name='quote_create'),
    path('quotes/<int:quote_id>/convert/', views.quote_convert_view, name='quote_convert'),

    path('invoices/', views.invoice_list_view, name='invoice_list'),
    path('invoices/create/', views.invoice_create_view, name='invoice_create'),
    path('invoices/<int:invoice_id>/', views.invoice_detail_view, name='invoice_detail'),
]
