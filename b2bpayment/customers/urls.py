from django.urls import path
from .views import CustomerListView, CustomerCreateView, CustomerUpdateView, CustomerDetailView, CustomerPublicDetailView

app_name = 'customers'

urlpatterns = [
    path('', CustomerListView.as_view(), name='list'),
    path('add/', CustomerCreateView.as_view(), name='create'),
    path('<int:pk>/', CustomerDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', CustomerUpdateView.as_view(), name='edit'),
    path('p/<int:pk>/', CustomerPublicDetailView.as_view(), name='public_detail'),
]
