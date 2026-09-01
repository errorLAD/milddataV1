from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime

from apps.people.models import (
    Employee, Attendance, LeaveRequest, EmployeeDocument, AttendanceStatus, LeaveStatus,
    SalaryPayment, SalaryPaymentMode, PayoutType
)
from apps.finance.models import Expense, ExpenseCategory
from apps.core.models import AuditLog

@login_required
def employee_list_view(request):
    org = request.organization
    employees = Employee.objects.filter(organization=org)
    return render(request, 'people/employee_list.html', {'employees': employees})

@login_required
def employee_create_view(request):
    org = request.organization
    if request.method == 'POST':
        emp = Employee.objects.create(
            organization=org,
            name=request.POST.get('name'),
            job_title=request.POST.get('job_title'),
            department=request.POST.get('department'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            start_date=request.POST.get('start_date') or timezone.now().date(),
            basic_salary=float(request.POST.get('basic_salary', 0.0))
        )
        AuditLog.objects.create(
            organization=org, user=request.user, action="Employee Created",
            model_name="Employee", record_id=str(emp.id), details=f"Employee {emp.name} added."
        )
        return redirect('employee_list')
    return render(request, 'people/employee_form.html')

@login_required
def employee_detail_view(request, emp_id):
    org = request.organization
    emp = get_object_or_404(Employee, id=emp_id, organization=org)
    attendances = Attendance.objects.filter(employee=emp)[:10]
    leaves = LeaveRequest.objects.filter(employee=emp)
    docs = EmployeeDocument.objects.filter(employee=emp)
    salary_payments = SalaryPayment.objects.filter(employee=emp)
    total_salary_paid = salary_payments.aggregate(total=Sum('amount'))['total'] or 0.00

    return render(request, 'people/employee_detail.html', {
        'emp': emp,
        'attendances': attendances,
        'leaves': leaves,
        'docs': docs,
        'salary_payments': salary_payments,
        'total_salary_paid': total_salary_paid,
        'modes': SalaryPaymentMode.choices,
        'payout_types': PayoutType.choices
    })

@login_required
def attendance_list_view(request):
    org = request.organization
    date_str = request.GET.get('date')
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        target_date = timezone.now().date()

    employees = Employee.objects.filter(organization=org, status='ACTIVE')
    records = {a.employee_id: a for a in Attendance.objects.filter(organization=org, date=target_date)}

    emp_attendance = []
    for emp in employees:
        rec = records.get(emp.id)
        emp_attendance.append({
            'employee': emp,
            'status': rec.status if rec else 'PRESENT',
            'notes': rec.notes if rec else ''
        })

    if request.method == 'POST':
        for emp in employees:
            status_val = request.POST.get(f'status_{emp.id}', 'PRESENT')
            notes_val = request.POST.get(f'notes_{emp.id}', '')
            Attendance.objects.update_or_create(
                organization=org, employee=emp, date=target_date,
                defaults={'status': status_val, 'notes': notes_val}
            )
        return redirect(f'/people/attendance/?date={target_date}')

    return render(request, 'people/attendance_list.html', {'emp_attendance': emp_attendance, 'target_date': target_date, 'statuses': AttendanceStatus.choices})

@login_required
def leave_list_view(request):
    org = request.organization
    leaves = LeaveRequest.objects.filter(organization=org)
    return render(request, 'people/leave_list.html', {'leaves': leaves})

@login_required
def leave_create_view(request):
    org = request.organization
    if request.method == 'POST':
        emp_id = request.POST.get('employee_id')
        emp = get_object_or_404(Employee, id=emp_id, organization=org)
        LeaveRequest.objects.create(
            organization=org,
            employee=emp,
            leave_type=request.POST.get('leave_type'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            reason=request.POST.get('reason')
        )
        return redirect('leave_list')
    employees = Employee.objects.filter(organization=org, status='ACTIVE')
    return render(request, 'people/leave_form.html', {'employees': employees})

@login_required
def leave_action_view(request, leave_id, action):
    org = request.organization
    leave = get_object_or_404(LeaveRequest, id=leave_id, organization=org)
    if action == 'approve':
        leave.status = LeaveStatus.APPROVED
    elif action == 'reject':
        leave.status = LeaveStatus.REJECTED
    leave.save()
    return redirect('leave_list')

@login_required
def salary_payment_list_view(request):
    org = request.organization
    payments = SalaryPayment.objects.filter(organization=org)
    total_paid = payments.aggregate(total=Sum('amount'))['total'] or 0.00
    employees = Employee.objects.filter(organization=org, status='ACTIVE')

    return render(request, 'people/salary_payment_list.html', {
        'payments': payments,
        'total_paid': float(total_paid),
        'employees': employees,
        'modes': SalaryPaymentMode.choices,
        'payout_types': PayoutType.choices
    })

@login_required
def salary_payment_create_view(request):
    org = request.organization
    if request.method == 'POST':
        emp_id = request.POST.get('employee_id')
        emp = get_object_or_404(Employee, id=emp_id, organization=org)
        amt = float(request.POST.get('amount', 0.0))
        p_type = request.POST.get('payout_type', PayoutType.SALARY)
        p_date = request.POST.get('payment_date') or timezone.now().date()
        p_mode = request.POST.get('payment_mode', SalaryPaymentMode.BANK_TRANSFER)
        ref_num = request.POST.get('reference_number', '')
        notes = request.POST.get('notes', '')

        sp = SalaryPayment.objects.create(
            organization=org,
            employee=emp,
            amount=amt,
            payout_type=p_type,
            payment_date=p_date,
            payment_mode=p_mode,
            reference_number=ref_num,
            notes=notes
        )

        # Log expense under Salaries & Wages
        cat, _ = ExpenseCategory.objects.get_or_create(organization=org, name="Salaries & Wages")
        Expense.objects.create(
            organization=org,
            title=f"Staff Payout ({p_type}): {emp.name}",
            amount=amt,
            category=cat,
            date=p_date,
            payment_method=p_mode,
            vendor=emp.name,
            notes=f"Type: {p_type} | Ref: {ref_num} | Notes: {notes}"
        )

        AuditLog.objects.create(
            organization=org, user=request.user, action="Employee Payout Recorded",
            model_name="SalaryPayment", record_id=str(sp.id),
            details=f"Paid {org.currency_symbol}{amt} ({p_type}) to {emp.name} via {p_mode} on {p_date}."
        )

        next_url = request.POST.get('next') or 'salary_payment_list'
        if next_url == 'employee_detail':
            return redirect('employee_detail', emp_id=emp.id)
        return redirect('salary_payment_list')

    employees = Employee.objects.filter(organization=org, status='ACTIVE')
    return render(request, 'people/salary_payment_form.html', {
        'employees': employees,
        'modes': SalaryPaymentMode.choices,
        'payout_types': PayoutType.choices
    })
