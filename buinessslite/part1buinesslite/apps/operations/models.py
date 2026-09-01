from django.db import models
from django.contrib.auth.models import User
from apps.core.models import Organization

class TaskPriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'

class TaskStatus(models.TextChoices):
    TO_DO = 'TO_DO', 'To Do'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    DONE = 'DONE', 'Done'

class Task(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    due_date = models.DateField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=TaskPriority.choices, default=TaskPriority.MEDIUM)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.TO_DO)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', '-created_at']

    def __str__(self):
        return self.title

class EventType(models.TextChoices):
    LEAVE = 'LEAVE', 'Employee Leave'
    TASK = 'TASK', 'Task Due'
    APPOINTMENT = 'APPOINTMENT', 'Appointment'
    INVOICE_DUE = 'INVOICE_DUE', 'Invoice Due'
    PAYMENT_DUE = 'PAYMENT_DUE', 'Payment Due'
    DOC_EXPIRY = 'DOC_EXPIRY', 'Document Expiry'
    REMINDER = 'REMINDER', 'Reminder'

class CalendarEvent(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    event_type = models.CharField(max_length=30, choices=EventType.choices, default=EventType.REMINDER)
    related_link = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.title} ({self.start_time})"

class DocCategory(models.TextChoices):
    BUSINESS = 'BUSINESS', 'Business'
    EMPLOYEES = 'EMPLOYEES', 'Employees'
    SUPPLIERS = 'SUPPLIERS', 'Suppliers'
    CUSTOMERS = 'CUSTOMERS', 'Customers'
    CONTRACTS = 'CONTRACTS', 'Contracts'
    LICENSES = 'LICENSES', 'Licenses'
    INSURANCE = 'INSURANCE', 'Insurance'
    OTHER = 'OTHER', 'Other'

class BusinessDocument(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='business_documents')
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=DocCategory.choices, default=DocCategory.BUSINESS)
    related_record = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='business_docs/', blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.category})"
