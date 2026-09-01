from django.urls import path
from .views import (
    SupplierListView, SupplierDetailView, SupplierCreateView,
    SupplierUpdateView, SupplierDeleteView, SupplierPurchaseCreateView,
    SupplierPurchaseUpdateView, SupplierPurchaseDeleteView,
    SupplierPayableListView, SupplierPaymentCreateView,
    export_suppliers_csv, export_purchases_csv, export_payments_csv
)

app_name = 'suppliers'

urlpatterns = [
    path('', SupplierListView.as_view(), name='list'),
    path('create/', SupplierCreateView.as_view(), name='create'),
    path('<int:pk>/', SupplierDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', SupplierUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', SupplierDeleteView.as_view(), name='delete'),
    
    path('purchases/new/', SupplierPurchaseCreateView.as_view(), name='purchase_create'),
    path('purchases/<int:pk>/edit/', SupplierPurchaseUpdateView.as_view(), name='purchase_edit'),
    path('purchases/<int:pk>/delete/', SupplierPurchaseDeleteView.as_view(), name='purchase_delete'),
    path('payables/', SupplierPayableListView.as_view(), name='payable_list'),
    path('payments/new/', SupplierPaymentCreateView.as_view(), name='payment_create'),
    
    path('export/suppliers/', export_suppliers_csv, name='export_suppliers'),
    path('export/purchases/', export_purchases_csv, name='export_purchases'),
    path('export/payments/', export_payments_csv, name='export_payments'),
]
