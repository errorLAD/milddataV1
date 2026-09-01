from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("saas/", views.saas_directory, name="saas_directory"),
    path("saas/<slug:slug>/", views.saas_detail, name="saas_detail"),
    path("saas/<slug:slug>/launch/", views.saas_launch, name="saas_launch"),
    path("detail/", views.catalog, name="detail_index"),
    path("detail/<str:identifier>/", views.universal_product_detail, name="universal_detail"),
    path("book-demo/", views.book_demo, name="book_demo"),
    path("<int:pk>/", views.product_detail, name="detail"),
    path("payment/verify/", views.payment_verify, name="payment_verify"),
    path("payment/success/", views.payment_success, name="success"),
]
