from django.urls import path
from .views import (
    PromotionListView, PromotionDetailView, PromotionCreateView,
    PromotionUpdateView, PromotionDeleteView, PromotionImageDeleteView,
    PromotionSendView
)

app_name = 'promotions'

urlpatterns = [
    path('', PromotionListView.as_view(), name='list'),
    path('create/', PromotionCreateView.as_view(), name='create'),
    path('<int:pk>/', PromotionDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', PromotionUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', PromotionDeleteView.as_view(), name='delete'),
    path('image/<int:pk>/delete/', PromotionImageDeleteView.as_view(), name='image_delete'),
    path('<int:pk>/send/', PromotionSendView.as_view(), name='send'),
]
