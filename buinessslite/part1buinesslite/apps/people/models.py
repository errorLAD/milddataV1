from django.db import models
from apps.core.models import Organization

class EmployeeStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    ON_LEAVE = 'ON_LEAVE', 'On Leave'
    INACTIVE = 'INACTIVE', 'Inactive'

class Employee(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='employees')
    name = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='employees/', blank=True, null=True)
    job_title = models.CharField(max_length=150)
    department = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    start_date = models.DateField()
    status = models.CharField(max_length=20, choices=EmployeeStatus.choices, default=EmployeeStatus.ACTIVE)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.job_title}"

class AttendanceStatus(models.TextChoices):
    PRESENT = 'PRESENT', 'Present'
    ABSENT = 'ABSENT', 'Absent'
    LATE = 'LATE', 'Late'
    HALF_DAY = 'HALF_DAY', 'Half Day'
    REMOTE = 'REMOTE', 'Remote'

class Attendance(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='attendances')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    notes = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.name} - {self.date}: {self.status}"

class LeaveStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'

class LeaveType(models.TextChoices):
    ANNUAL = 'ANNUAL', 'Annual Leave'
    SICK = 'SICK', 'Sick Leave'
    CASUAL = 'CASUAL', 'Casual Leave'
    UNPAID = 'UNPAID', 'Unpaid Leave'

class LeaveRequest(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='leave_requests')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LeaveType.choices, default=LeaveType.ANNUAL)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=LeaveStatus.choices, default=LeaveStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.name} - {self.leave_type} ({self.start_date} to {self.end_date})"

class DocType(models.TextChoices):
    CONTRACT = 'CONTRACT', 'Contract'
    ID = 'ID', 'ID Card / Passport'
    CERTIFICATION = 'CERTIFICATION', 'Certification'
    LICENSE = 'LICENSE', 'License'
    OTHER = 'OTHER', 'Other'

class EmployeeDocument(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='employee_documents')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=20, choices=DocType.choices, default=DocType.CONTRACT)
    file = models.FileField(upload_to='emp_docs/', blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.employee.name}"

class SalaryPaymentMode(models.TextChoices):
    BANK_TRANSFER = 'Bank Transfer', 'Online Bank Transfer'
    UPI_ONLINE = 'UPI / Online', 'UPI / Net Banking'
    CASH = 'Cash', 'Cash'
    CHECK = 'Check', 'Check'
    CARD = 'Card', 'Card'
    OTHER = 'Other', 'Other'

class PayoutType(models.TextChoices):
    SALARY = 'Salary', 'Monthly Salary'
    DAILY_WAGE = 'Daily Wage', 'Daily Wage'
    WEEKLY_WAGE = 'Weekly Wage', 'Weekly Wage'
    TASK_PAY = 'Task / Piece Work', 'Task / Piece Work Pay'
    ADVANCE = 'Advance', 'Salary Advance'
    COMMISSION = 'Commission / Bonus', 'Commission / Bonus'

class SalaryPayment(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='salary_payments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payout_type = models.CharField(max_length=50, choices=PayoutType.choices, default=PayoutType.SALARY)
    payment_date = models.DateField()
    payment_time = models.TimeField(auto_now_add=True)
    payment_mode = models.CharField(max_length=50, choices=SalaryPaymentMode.choices, default=SalaryPaymentMode.BANK_TRANSFER)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"{self.employee.name}: {self.amount} ({self.payout_type}) via {self.payment_mode} on {self.payment_date}"
