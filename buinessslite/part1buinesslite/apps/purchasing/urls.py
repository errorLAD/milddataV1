from django.urls import path
from apps.purchasing import views

urlpatterns = [
    path('suppliers/', views.supplier_list_view, name='supplier_list'),
    path('suppliers/create/', views.supplier_create_view, name='supplier_create'),
    path('suppliers/<int:supp_id>/', views.supplier_detail_view, name='supplier_detail'),
    path('orders/', views.po_list_view, name='po_list'),
    path('orders/create/', views.po_create_view, name='po_create'),
    path('orders/<int:po_id>/', views.po_detail_view, name='po_detail'),
    path('orders/<int:po_id>/receive/', views.receive_goods_view, name='receive_goods'),
]
