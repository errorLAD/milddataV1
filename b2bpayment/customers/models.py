from django.db import models
from django.db.models import Sum
from django.utils import timezone
from core.models import TenantModel
from .utils import calculate_trust_score

class Customer(TenantModel):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Blocked', 'Blocked'),
    )

    name = models.CharField(max_length=255, verbose_name="Customer Name")
    phone = models.CharField(max_length=20, verbose_name="Phone Number")
    email = models.EmailField(blank=True, null=True, verbose_name="Email Address")
    address = models.TextField(blank=True, verbose_name="Customer Address")
    notes = models.TextField(blank=True, verbose_name="Internal Notes")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    # Advanced SaaS Features
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True, verbose_name="Credit Limit (₹, 0 = No Limit)")
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals', verbose_name="Referred By Customer")
    promises_broken_count = models.IntegerField(default=0, verbose_name="Broken Promises Count")
    accepts_marketing = models.BooleanField(default=True, verbose_name="Opted-in for WhatsApp Broadcasts")
    tags = models.ManyToManyField('whatsapp.Tag', blank=True, related_name='customers')

    class Meta:
        ordering = ['-created_at']
        unique_together = ['business', 'phone']

    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def trust_score(self):
        return calculate_trust_score(self)

    @property
    def get_total_sales_amount(self):
        sales_total = self.sales.aggregate(total=Sum('total_amount'))['total'] or 0
        return sales_total

    @property
    def get_total_paid_amount(self):
        payments_total = self.payments.aggregate(total=Sum('amount'))['total'] or 0
        return payments_total

    @property
    def get_outstanding_udhaar(self):
        udhaar_total = self.udhaars.exclude(status='Paid').aggregate(total=Sum('remaining_amount'))['total'] or 0
        return udhaar_total

    @property
    def get_overdue_udhaar(self):
        today = timezone.now().date()
        overdue_total = self.udhaars.filter(due_date__lt=today).exclude(status='Paid').aggregate(total=Sum('remaining_amount'))['total'] or 0
        return overdue_total

    @property
    def get_last_purchase_date(self):
        last_sale = self.sales.order_by('-sale_date').first()
        return last_sale.sale_date if last_sale else None

    @property
    def credit_limit_used_percent(self):
        if not self.credit_limit or self.credit_limit <= 0:
            return 0
        outstanding = self.get_outstanding_udhaar
        percent = (float(outstanding) / float(self.credit_limit)) * 100
        return min(100, round(percent, 1))

    @property
    def is_credit_limit_exceeded(self):
        if not self.credit_limit or self.credit_limit <= 0:
            return False
        return self.get_outstanding_udhaar > self.credit_limit

    @property
    def risk_score(self):
        """
        Rule-Based Risk Score Evaluation Engine:
        Inputs:
          1. Overdue Udhaar entries count
          2. Overdue ratio = Overdue Amount / Total Sales Amount
          3. Broken promises count (promises_broken_count)
          4. Average days overdue

        Thresholds:
          - High Risk: Broken promises >= 3 OR Overdue entries >= 3 OR Overdue ratio > 40%
          - Medium Risk: Broken promises >= 1 OR Overdue entries >= 1 OR Overdue ratio > 15%
          - Low Risk: Clear history / prompt payments
        """
        today = timezone.now().date()
        overdue_entries = self.udhaars.filter(due_date__lt=today).exclude(status='Paid')
        overdue_count = overdue_entries.count()
        
        total_sales = float(self.get_total_sales_amount)
        overdue_amt = float(self.get_overdue_udhaar)
        overdue_ratio = (overdue_amt / total_sales) if total_sales > 0 else (1.0 if overdue_amt > 0 else 0.0)

        if self.promises_broken_count >= 3 or overdue_count >= 3 or overdue_ratio >= 0.4:
            return {
                'level': 'High Risk',
                'badge_class': 'bg-danger text-white',
                'description': 'Frequent overdue payments or multiple broken promises.'
            }
        elif self.promises_broken_count >= 1 or overdue_count >= 1 or overdue_ratio >= 0.15:
            return {
                'level': 'Medium Risk',
                'badge_class': 'bg-warning text-dark',
                'description': 'Occasional delayed payments.'
            }
        return {
            'level': 'Low Risk',
            'badge_class': 'bg-success text-white',
            'description': 'Excellent payment track record.'
        }
