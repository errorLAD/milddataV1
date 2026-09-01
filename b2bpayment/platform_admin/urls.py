from django.urls import path
from .views import (
    AdminDashboardView, BusinessListView, BusinessDetailView,
    BlockBusinessView, UnblockBusinessView, DeleteBusinessView,
    AIMetricsView
)

app_name = 'platform_admin'

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='dashboard'),
    path('businesses/', BusinessListView.as_view(), name='business_list'),
    path('businesses/<int:pk>/', BusinessDetailView.as_view(), name='business_detail'),
    path('businesses/<int:pk>/block/', BlockBusinessView.as_view(), name='business_block'),
    path('businesses/<int:pk>/unblock/', UnblockBusinessView.as_view(), name='business_unblock'),
    path('businesses/<int:pk>/delete/', DeleteBusinessView.as_view(), name='business_delete'),
    path('ai-metrics/', AIMetricsView.as_view(), name='ai_metrics'),
]
