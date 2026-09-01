from django.urls import path
from .views import DashboardIndexView, SimpleDashboardView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardIndexView.as_view(), name='index'),
    path('simple/', SimpleDashboardView.as_view(), name='simple'),
]

