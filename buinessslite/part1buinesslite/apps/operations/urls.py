from django.urls import path
from apps.operations import views

urlpatterns = [
    path('tasks/', views.task_list_view, name='task_list'),
    path('tasks/create/', views.task_create_view, name='task_create'),
    path('tasks/<int:task_id>/status/', views.update_task_status_view, name='update_task_status'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('documents/', views.business_document_list_view, name='business_document_list'),
    path('documents/upload/', views.document_upload_view, name='document_upload'),
]
