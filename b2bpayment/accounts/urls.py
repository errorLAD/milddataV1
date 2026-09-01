from django.urls import path
from .views import RegisterView, LoginView, LogoutView, GuestLoginView, UpgradeGuestView

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('guest-login/', GuestLoginView.as_view(), name='guest_login'),
    path('upgrade-guest/', UpgradeGuestView.as_view(), name='upgrade_guest'),
]

