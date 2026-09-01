from django.urls import path
from . import views

urlpatterns = [
    path('', views.support_index, name='support_index'),
    path('ticket/', views.submit_ticket, name='submit_ticket'),
]
