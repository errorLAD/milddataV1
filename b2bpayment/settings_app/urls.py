from django.urls import path
from .views import SettingsView, TestAIConnectionView

app_name = 'settings_app'

urlpatterns = [
    path('', SettingsView.as_view(), name='index'),
    path('test-ai/', TestAIConnectionView.as_view(), name='test_ai'),
]
