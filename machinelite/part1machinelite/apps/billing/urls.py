from django.urls import path
from . import views

urlpatterns = [
    path('', views.billing_plans_view, name='billing_plans'),
    path('upgrade-tier/', views.upgrade_plan, name='upgrade_plan_tier'),
]
