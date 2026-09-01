from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("guest/", views.guest_login, name="guest_login"),
    path("logout/", views.logout_view, name="logout"),
]
