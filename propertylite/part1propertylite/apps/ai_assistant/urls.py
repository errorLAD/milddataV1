from django.urls import path
from . import views

urlpatterns = [
    path('', views.ai_chat_view, name='ai_chat'),
    path('api/query/', views.ai_query_api, name='ai_query_api'),
]
