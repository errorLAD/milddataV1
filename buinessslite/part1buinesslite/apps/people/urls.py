from django.urls import path
from apps.people import views

urlpatterns = [
    path('employees/', views.employee_list_view, name='employee_list'),
    path('employees/create/', views.employee_create_view, name='employee_create'),
    path('employees/<int:emp_id>/', views.employee_detail_view, name='employee_detail'),
    path('attendance/', views.attendance_list_view, name='attendance_list'),
    path('leave/', views.leave_list_view, name='leave_list'),
    path('leave/create/', views.leave_create_view, name='leave_create'),
    path('leave/<int:leave_id>/<str:action>/', views.leave_action_view, name='leave_action'),
    path('salaries/', views.salary_payment_list_view, name='salary_payment_list'),
    path('salaries/create/', views.salary_payment_create_view, name='salary_payment_create'),
]
