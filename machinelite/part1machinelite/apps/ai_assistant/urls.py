from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='ai_assistant_chat'),
    path('api/ask/', views.ask_api, name='ai_assistant_ask_api'),
]
