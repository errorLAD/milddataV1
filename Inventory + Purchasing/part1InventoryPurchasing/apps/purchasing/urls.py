from django.urls import path
from apps.purchasing import views

urlpatterns = [
    path('suppliers/', views.supplier_list_view, name='supplier_list'),
    path('suppliers/create/', views.supplier_create_view, name='supplier_create'),
    path('suppliers/<int:supplier_id>/', views.supplier_detail_view, name='supplier_detail'),

    path('pos/', views.po_list_view, name='po_list'),
    path('pos/create/', views.po_create_view, name='po_create'),
    path('pos/<int:po_id>/', views.po_detail_view, name='po_detail'),
    path('pos/<int:po_id>/status/', views.po_status_update_view, name='po_status_update'),
    path('pos/<int:po_id>/receive/', views.goods_receipt_create_view, name='goods_receipt'),
]
