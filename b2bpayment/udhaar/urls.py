from django.urls import path
from .views import (
    UdhaarListView, UdhaarDetailView, UdhaarCreateView,
    RecordPartialPaymentView, ChangeDueDateView, SetPromiseView, SendReminderView
)

app_name = 'udhaar'

urlpatterns = [
    path('', UdhaarListView.as_view(), name='list'),
    path('add/', UdhaarCreateView.as_view(), name='create'),
    path('<int:pk>/', UdhaarDetailView.as_view(), name='detail'),
    path('<int:pk>/pay/', RecordPartialPaymentView.as_view(), name='record_payment'),
    path('<int:pk>/due-date/', ChangeDueDateView.as_view(), name='change_due_date'),
    path('<int:pk>/promise/', SetPromiseView.as_view(), name='set_promise'),
    path('<int:pk>/reminder/', SendReminderView.as_view(), name='send_reminder'),
]
