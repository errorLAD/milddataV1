from django.urls import path
from . import views

urlpatterns = [
    path('api/', views.global_search_api, name='global_search_api'),
]
