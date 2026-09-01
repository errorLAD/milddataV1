from django.urls import path
from apps.sales import views

urlpatterns = [
    path('customers/', views.customer_list_view, name='customer_list'),
    path('customers/create/', views.customer_create_view, name='customer_create'),
    path('customers/<int:cust_id>/', views.customer_detail_view, name='customer_detail'),
    path('quotes/', views.quote_list_view, name='quote_list'),
    path('quotes/create/', views.quote_create_view, name='quote_create'),
    path('quotes/<int:quote_id>/convert/', views.convert_quote_to_order, name='convert_quote_to_order'),
    path('orders/', views.sales_order_list_view, name='sales_order_list'),
    path('invoices/', views.invoice_list_view, name='invoice_list'),
    path('invoices/create/', views.invoice_create_view, name='invoice_create'),
    path('invoices/<int:inv_id>/', views.invoice_detail_view, name='invoice_detail'),
    path('invoices/<int:inv_id>/pay/', views.record_payment_view, name='record_payment'),
    path('invoices/<int:inv_id>/pdf/', views.invoice_pdf_view, name='invoice_pdf'),
    path('payments/<int:pay_id>/receipt/', views.payment_receipt_view, name='payment_receipt'),
]
