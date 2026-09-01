from django.urls import path

from . import views

app_name = "labeling"

urlpatterns = [
    path("", views.home, name="home"),
]
