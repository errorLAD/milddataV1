from django.urls import path
from .views import SaleListView, SaleCreateView, SaleDetailView, SaleInvoicePDFView

app_name = 'sales'

urlpatterns = [
    path('', SaleListView.as_view(), name='list'),
    path('add/', SaleCreateView.as_view(), name='create'),
    path('<int:pk>/', SaleDetailView.as_view(), name='detail'),
    path('<int:pk>/pdf/', SaleInvoicePDFView.as_view(), name='pdf_invoice'),
]
