from django.urls import path
from . import views

urlpatterns = [
    path('', views.billing_index, name='billing'),
]
