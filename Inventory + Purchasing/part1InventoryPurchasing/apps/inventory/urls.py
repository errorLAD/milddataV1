from django.urls import path
from apps.inventory import views

urlpatterns = [
    path('products/', views.product_list_view, name='product_list'),
    path('products/create/', views.product_create_view, name='product_create'),
    path('products/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('products/<int:product_id>/edit/', views.product_edit_view, name='product_edit'),
    path('products/<int:product_id>/archive/', views.product_archive_view, name='product_archive'),
    path('warehouses/', views.warehouse_list_view, name='warehouse_list'),
    path('movements/', views.stock_movements_view, name='stock_movements'),
    path('transfer/', views.stock_transfer_view, name='stock_transfer'),
    path('adjustment/', views.stock_adjustment_view, name='stock_adjustment'),
]
