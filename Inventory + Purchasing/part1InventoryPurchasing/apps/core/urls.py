from django.urls import path
from apps.core import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/search/', views.search_api, name='search_api'),
    path('api/barcode-lookup/', views.barcode_lookup_api, name='barcode_lookup_api'),
    path('seed-demo-data/', views.trigger_seed_demo_data, name='seed_demo_data'),
    path('api/notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),

    # StockFlow AI Routes
    path('api/ai/copilot/', views.ai_copilot_api, name='ai_copilot_api'),
    path('settings/ai/', views.ai_settings_view, name='ai_settings'),
    path('api/ai/test/', views.test_ai_connection_api, name='test_ai_connection_api'),
]
