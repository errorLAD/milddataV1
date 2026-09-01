import json
import datetime
from django.shortcuts import render
from django.views import View
from django.db.models import Sum, Count, Q
from django.utils import timezone

from core.mixins import TenantRequiredMixin
from sales.models import Sale, SaleItem
from udhaar.models import Udhaar
from customers.models import Customer
from payments.models import Payment


class LandingPageView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'landing.html')


def get_collection_priority(udhaar_record, today=None):
    """
    Inline priority scoring — duplicated here to avoid circular import
    with Python's built-in 'collections' module shadowing our app.
    """
    from django.utils import timezone as tz
    if today is None:
        today = tz.now().date()

    score = 0
    days_over = udhaar_record.days_overdue
    amount = float(udhaar_record.remaining_amount)
    missed = udhaar_record.customer.promises_broken_count
    is_promised = udhaar_record.status == 'Payment Promised'
    promise_missed_flag = (
        udhaar_record.promised_date
        and udhaar_record.promised_date < today
        and udhaar_record.status not in ['Paid']
        and not is_promised
    )

    score += min(days_over * 2, 60)
    score += min(amount / 10000, 30)
    score += missed * 10
    if promise_missed_flag:
        score += 20

    if score >= 60 or (days_over >= 30 and missed >= 1):
        return {'level': 'Urgent', 'color': 'danger', 'icon': '🔴', 'score': score}
    elif score >= 30 or days_over >= 10:
        return {'level': 'High', 'color': 'warning', 'icon': '🟠', 'score': score}
    elif days_over > 0:
        return {'level': 'Normal', 'color': 'info', 'icon': '🟡', 'score': score}
    else:
        return {'level': 'Low', 'color': 'success', 'icon': '🟢', 'score': score}



class DashboardIndexView(TenantRequiredMixin, View):
    """
    B2B Payment Collections Dashboard — Collections-first layout.
    Primary metric: Total Outstanding (not Net Money Position).
    Core sections: Outstanding summary, Today's Collection Tasks, Recent Activity.
    """
    def get(self, request):
        business = request.business
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        next_7_days = today + datetime.timedelta(days=7)

        # -------------------------------------------------------
        # 1. Collections Overview (primary hero metrics)
        # -------------------------------------------------------
        all_udhaars = Udhaar.objects.filter(business=business)
        active_udhaars = all_udhaars.exclude(status='Paid')

        # Auto-update overdue statuses
        for u in active_udhaars.filter(due_date__lt=today).exclude(
            status__in=['Overdue', 'Payment Promised', 'Partially Paid', 'Disputed']
        ):
            u.status = 'Overdue'
            u.save(update_fields=['status'])

        # Refresh qs after update
        active_udhaars = all_udhaars.exclude(status='Paid')

        total_outstanding = active_udhaars.aggregate(s=Sum('remaining_amount'))['s'] or 0
        overdue_amount = active_udhaars.filter(due_date__lt=today).aggregate(s=Sum('remaining_amount'))['s'] or 0
        due_today_amount = active_udhaars.filter(due_date=today).aggregate(s=Sum('remaining_amount'))['s'] or 0
        upcoming_amount = active_udhaars.filter(due_date__gt=today).aggregate(s=Sum('remaining_amount'))['s'] or 0

        # -------------------------------------------------------
        # 2. Today's Priority Collection Tasks
        # -------------------------------------------------------
        # Customers needing follow-up today = overdue + due today
        priority_udhaars = active_udhaars.filter(due_date__lte=today).select_related('customer', 'sale').order_by('due_date')

        # Annotate priority
        priority_list = []
        for u in priority_udhaars[:20]:
            u.priority = get_collection_priority(u, today)
            priority_list.append(u)

        # Sort by priority score
        priority_list.sort(key=lambda r: -r.priority['score'])

        potential_today = sum(float(u.remaining_amount) for u in priority_list)
        customers_needing_followup = active_udhaars.filter(due_date__lte=today).values('customer').distinct().count()

        # -------------------------------------------------------
        # 3. Promises Due Today
        # -------------------------------------------------------
        promises_due_today = active_udhaars.filter(
            status='Payment Promised',
            promised_date=today
        ).select_related('customer')[:5]

        # Missed promises
        missed_promises = active_udhaars.filter(
            promise_broken=True
        ).count()

        # -------------------------------------------------------
        # 4. Upcoming Collections (next 7 days)
        # -------------------------------------------------------
        upcoming_collections = active_udhaars.filter(
            due_date__gt=today,
            due_date__lte=next_7_days
        ).order_by('due_date').select_related('customer')[:8]

        # -------------------------------------------------------
        # 5. Recent Activity
        # -------------------------------------------------------
        recent_payments = Payment.objects.filter(
            business=business
        ).order_by('-created_at').select_related('customer')[:6]

        # -------------------------------------------------------
        # 6. Collection Performance Chart (last 30 days)
        # -------------------------------------------------------
        chart_labels = []
        chart_collected = []
        chart_outstanding_daily = []

        for i in range(29, -1, -1):
            d = today - datetime.timedelta(days=i)
            if i % 5 == 0 or i == 0:  # label every 5 days
                chart_labels.append(d.strftime('%d %b'))
            else:
                chart_labels.append('')

            day_collected = Payment.objects.filter(
                business=business, created_at__date=d
            ).aggregate(s=Sum('amount'))['s'] or 0
            chart_collected.append(float(day_collected))

            day_overdue = all_udhaars.filter(due_date__lte=d).exclude(status='Paid').aggregate(
                s=Sum('remaining_amount')
            )['s'] or 0
            chart_outstanding_daily.append(float(day_overdue))

        # -------------------------------------------------------
        # 7. Customer & Sales summary (secondary)
        # -------------------------------------------------------
        total_customers = Customer.objects.filter(business=business).count()
        customers_with_outstanding = active_udhaars.values('customer').distinct().count()

        # Monthly collections (this month)
        collected_this_month = Payment.objects.filter(
            business=business,
            created_at__date__gte=first_day_of_month
        ).aggregate(s=Sum('amount'))['s'] or 0

        # Collection rate
        total_billed = all_udhaars.aggregate(s=Sum('total_amount'))['s'] or 0
        total_collected_all = all_udhaars.aggregate(s=Sum('paid_amount'))['s'] or 0
        collection_rate = round(
            (float(total_collected_all) / float(total_billed) * 100), 1
        ) if total_billed else 0

        from settings_app.models import BusinessSettings
        b_settings, _ = BusinessSettings.objects.get_or_create(business=business)
        currency_symbol = b_settings.currency_symbol or '$' if b_settings.currency == 'USD' else '₹'

        context = {
            'currency_symbol': currency_symbol,
            'currency': b_settings.currency,
            # Hero metrics
            'total_outstanding': total_outstanding,
            'overdue_amount': overdue_amount,
            'due_today_amount': due_today_amount,
            'upcoming_amount': upcoming_amount,
            'customers_needing_followup': customers_needing_followup,

            # Today's tasks
            'priority_list': priority_list[:10],
            'potential_today': potential_today,
            'promises_due_today': promises_due_today,
            'missed_promises': missed_promises,

            # Upcoming
            'upcoming_collections': upcoming_collections,

            # Activity
            'recent_payments': recent_payments,

            # Stats
            'total_customers': total_customers,
            'customers_with_outstanding': customers_with_outstanding,
            'collected_this_month': collected_this_month,
            'collection_rate': collection_rate,

            # Chart data
            'chart_labels': json.dumps(chart_labels),
            'chart_collected': json.dumps(chart_collected),

            'today': today,
        }

        return render(request, 'dashboard/dashboard.html', context)


# Alias for backward compatibility
SimpleDashboardView = DashboardIndexView
