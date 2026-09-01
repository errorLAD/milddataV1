from django.urls import path
from . import views

app_name = 'collections'

urlpatterns = [
    # Main collections list with tab filters
    path('', views.CollectionsListView.as_view(), name='list'),

    # Bulk reminder (Send All Reminders button)
    path('send-bulk-reminders/', views.SendBulkRemindersView.as_view(), name='send_bulk_reminders'),
    path('bulk-remind/', views.SendBulkRemindersView.as_view(), name='bulk_remind'),

    # Single reminder (per collection record)
    path('<int:pk>/remind/', views.SendSingleReminderView.as_view(), name='send_reminder'),

    # Promise to Pay
    path('<int:pk>/promise/', views.SetPromiseView.as_view(), name='set_promise'),

    # Reports
    path('reports/', views.CollectionReportsView.as_view(), name='reports'),

    # Reminder Rules configuration
    path('reminder-rules/', views.ReminderRulesView.as_view(), name='reminder_rules'),

    # Dashboard data API
    path('api/dashboard-data/', views.CollectionsDashboardDataView.as_view(), name='dashboard_data'),
]
