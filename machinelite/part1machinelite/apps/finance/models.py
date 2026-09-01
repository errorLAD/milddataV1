from django.db import models
from apps.tenants.models import Organization
from apps.machines.models import Machine
from apps.projects.models import Project

class RevenueLog(models.Model):
    BILLING_TYPE_CHOICES = (
        ('hourly', 'Hourly Rate Billing'),
        ('daily', 'Daily Rental Rate'),
        ('monthly_contract', 'Monthly Dedicated Contract'),
        ('fixed_job', 'Fixed Project Milestone'),
    )

    STATUS_CHOICES = (
        ('paid', 'Paid / Settled'),
        ('billed', 'Invoiced / Pending'),
        ('overdue', 'Overdue Payment'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='revenue_logs')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='revenue_logs')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='revenue_logs')
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    hours_billed = models.FloatField(default=0.0, help_text="Hours or days operated for this invoice")
    billing_type = models.CharField(max_length=30, choices=BILLING_TYPE_CHOICES, default='hourly')
    client_name = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='paid')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.machine.name} - ₹{self.amount} ({self.client_name})"

class ExpenseLog(models.Model):
    CATEGORY_CHOICES = (
        ('fuel', 'Fuel Expense'),
        ('maintenance', 'Parts & Service Maintenance'),
        ('operator_salary', 'Operator Wages / Allowance'),
        ('transport', 'Machine Towing & Transport'),
        ('emi_lease', 'Machine Loan EMI / Lease'),
        ('other', 'General Operating Expense'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='expense_logs')
    machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True, related_name='expense_logs')
    date = models.DateField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='maintenance')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    vendor_recipient = models.CharField(max_length=150, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        target = self.machine.name if self.machine else "General Fleet"
        return f"{target} - {self.get_category_display()}: ₹{self.amount}"
