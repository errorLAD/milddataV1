from django.urls import path
from . import views

urlpatterns = [
    path('', views.settings_view, name='settings_index'),
    path('localization/', views.update_localization, name='update_localization'),
]
