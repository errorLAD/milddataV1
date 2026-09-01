from django.urls import path
from .views import MarkAllReadView

app_name = 'notifications'

urlpatterns = [
    path('mark-all-read/', MarkAllReadView.as_view(), name='mark_all_read'),
]
