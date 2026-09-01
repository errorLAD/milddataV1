from django.urls import path
from .views import ProductListView, ProductCreateView, ProductUpdateView

app_name = 'products'

urlpatterns = [
    path('', ProductListView.as_view(), name='list'),
    path('add/', ProductCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', ProductUpdateView.as_view(), name='edit'),
]
