from django.urls import path
from apps.inventory import views

urlpatterns = [
    path('products/', views.product_list_view, name='product_list'),
    path('products/create/', views.product_create_view, name='product_create'),
    path('products/<int:prod_id>/', views.product_detail_view, name='product_detail'),
    path('products/<int:prod_id>/adjust/', views.stock_adjust_view, name='stock_adjust'),
    path('movements/', views.stock_movement_list_view, name='movement_list'),
    path('barcode/', views.barcode_scanner_view, name='barcode_scanner'),
    path('api/barcode-lookup/', views.barcode_lookup_api, name='barcode_lookup_api'),
]
