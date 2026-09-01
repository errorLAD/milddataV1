import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.http import JsonResponse
from django.contrib import messages

from core.mixins import TenantRequiredMixin
from udhaar.models import Udhaar
from customers.models import Customer
from payments.models import Payment
from whatsapp.models import WhatsAppConversation, WhatsAppMessage, WhatsAppMessageTemplate
from .models import ReminderRule, CollectionActivity


# ---------------------------------------------------------------------------
# Helper: Priority scoring for collection customers
# ---------------------------------------------------------------------------

def get_collection_priority(udhaar_record, today=None):
    """
    Returns a priority dict: level (Urgent/High/Normal/Low), score, color.
    Score based on: amount overdue, days overdue, missed promises, promise status.
    """
    if today is None:
        today = timezone.now().date()

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

    # Scoring
    score += min(days_over * 2, 60)           # max 60 from days overdue
    score += min(amount / 10000, 30)           # max 30 from amount (₹3L+ = 30)
    score += missed * 10                       # 10 per broken promise
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


# ---------------------------------------------------------------------------
# Collections List View
# ---------------------------------------------------------------------------

class CollectionsListView(TenantRequiredMixin, View):
    """
    Main B2B Collections page — replaces the old Udhaar list as the primary
    collections interface. Supports filter tabs: All / Overdue / Due Today /
    Upcoming / Promise to Pay / Missed Promise / Paid.
    """
    template_name = 'collections/collections_list.html'
    paginate_by = 30

    def get(self, request):
        business = request.business
        today = timezone.now().date()
        tab = request.GET.get('tab', 'all')
        search = request.GET.get('q', '').strip()

        # Base queryset — real-time overdue status update
        all_udhaars = Udhaar.objects.filter(business=business).select_related('customer', 'sale')

        # Auto-update overdue statuses
        pending_qs = all_udhaars.exclude(status__in=['Paid', 'Disputed'])
        for u in pending_qs.filter(due_date__lt=today).exclude(status__in=['Overdue', 'Payment Promised', 'Partially Paid']):
            u.status = 'Overdue'
            u.save(update_fields=['status'])

        # Check missed promises
        for u in pending_qs.filter(
            status='Payment Promised',
            promised_date__lt=today
        ):
            u.promise_broken = True
            u.status = 'Overdue'
            u.save(update_fields=['status', 'promise_broken'])
            u.customer.promises_broken_count = (u.customer.promises_broken_count or 0) + 1
            u.customer.save(update_fields=['promises_broken_count'])
            CollectionActivity.objects.get_or_create(
                business=business,
                udhaar=u,
                activity_type='promise_missed',
                defaults={
                    'description': f"Promise missed — was due on {u.promised_date.strftime('%d %b %Y')}",
                    'performed_by': 'System Auto'
                }
            )

        # Re-fetch after updates
        qs = Udhaar.objects.filter(business=business).select_related('customer', 'sale')

        # Search
        if search:
            qs = qs.filter(
                Q(customer__name__icontains=search) |
                Q(customer__phone__icontains=search) |
                Q(sale__invoice_number__icontains=search)
            )

        # Tab filter
        if tab == 'overdue':
            qs = qs.filter(due_date__lt=today).exclude(status='Paid')
        elif tab == 'due_today':
            qs = qs.filter(due_date=today).exclude(status='Paid')
        elif tab == 'upcoming':
            qs = qs.filter(due_date__gt=today).exclude(status='Paid')
        elif tab == 'promise':
            qs = qs.filter(status='Payment Promised')
        elif tab == 'missed':
            qs = qs.filter(promise_broken=True).exclude(status='Paid')
        elif tab == 'paid':
            qs = qs.filter(status='Paid')
        else:  # 'all' — exclude paid by default, show all active
            qs = qs.exclude(status='Paid')

        # Summary counts for tab badges
        all_active = Udhaar.objects.filter(business=business).exclude(status='Paid')
        counts = {
            'all': all_active.count(),
            'overdue': all_active.filter(due_date__lt=today).count(),
            'due_today': all_active.filter(due_date=today).count(),
            'upcoming': all_active.filter(due_date__gt=today).count(),
            'promise': Udhaar.objects.filter(business=business, status='Payment Promised').count(),
            'missed': Udhaar.objects.filter(business=business, promise_broken=True).exclude(status='Paid').count(),
            'paid': Udhaar.objects.filter(business=business, status='Paid').count(),
        }

        # Summary amounts
        total_outstanding = all_active.aggregate(s=Sum('remaining_amount'))['s'] or 0
        overdue_amount = all_active.filter(due_date__lt=today).aggregate(s=Sum('remaining_amount'))['s'] or 0
        due_today_amount = all_active.filter(due_date=today).aggregate(s=Sum('remaining_amount'))['s'] or 0
        upcoming_amount = all_active.filter(due_date__gt=today).aggregate(s=Sum('remaining_amount'))['s'] or 0

        # Annotate priority for each record
        records = list(qs.order_by('due_date', '-remaining_amount'))
        for record in records:
            record.priority = get_collection_priority(record, today)

        # Sort by priority score descending
        records.sort(key=lambda r: -r.priority['score'])

        # Pagination (manual, simple)
        page = int(request.GET.get('page', 1))
        per_page = self.paginate_by
        total_count = len(records)
        start = (page - 1) * per_page
        end = start + per_page
        page_records = records[start:end]
        total_pages = (total_count + per_page - 1) // per_page

        templates = WhatsAppMessageTemplate.objects.filter(
            business=business,
            trigger_type__in=['Due Reminder', 'Overdue Reminder', 'Promise Confirmation']
        )

        context = {
            'records': page_records,
            'tab': tab,
            'counts': counts,
            'search': search,
            'total_outstanding': total_outstanding,
            'overdue_amount': overdue_amount,
            'due_today_amount': due_today_amount,
            'upcoming_amount': upcoming_amount,
            'today': today,
            'page': page,
            'total_pages': total_pages,
            'total_count': total_count,
            'templates': templates,
        }
        return render(request, self.template_name, context)


# ---------------------------------------------------------------------------
# Send Bulk Reminders View
# ---------------------------------------------------------------------------

class SendBulkRemindersView(TenantRequiredMixin, View):
    """
    Send WhatsApp reminders to all overdue/due-today customers at once.
    """
    def post(self, request):
        business = request.business
        today = timezone.now().date()
        target = request.POST.get('target', 'overdue')  # 'overdue' or 'due_today'

        if target == 'due_today':
            udhaars = Udhaar.objects.filter(business=business, due_date=today).exclude(status='Paid')
        else:
            udhaars = Udhaar.objects.filter(business=business, due_date__lte=today).exclude(status='Paid')

        sent_count = 0
        for u in udhaars:
            # Rate limit: skip if reminder sent in last 24h
            if u.last_reminder_sent:
                hours_since = (timezone.now() - u.last_reminder_sent).total_seconds() / 3600
                if hours_since < 24:
                    continue

            conv, _ = WhatsAppConversation.objects.get_or_create(business=business, customer=u.customer)
            if u.days_overdue > 0:
                msg = f"Namaste {u.customer.name} ji, aapka ₹{u.remaining_amount:,.0f} ka payment {u.days_overdue} din se overdue hai. Kripya jald se jald payment karein. Dhanyawad."
            else:
                msg = f"Namaste {u.customer.name} ji, aaj aapke ₹{u.remaining_amount:,.0f} ka payment due hai. Kripya payment karein. Dhanyawad."

            WhatsAppMessage.objects.create(
                conversation=conv,
                sender='business',
                message_text=msg,
                status='Sent'
            )
            u.last_reminder_sent = timezone.now()
            u.save(update_fields=['last_reminder_sent'])

            CollectionActivity.objects.create(
                business=business,
                udhaar=u,
                activity_type='reminder_sent',
                description=f"Bulk WhatsApp reminder sent",
                performed_by=request.user.username
            )
            sent_count += 1

        messages.success(request, f"✅ WhatsApp reminders sent to {sent_count} customer(s)!")
        return redirect('collections:list')


# ---------------------------------------------------------------------------
# Send Single Reminder (AJAX-friendly)
# ---------------------------------------------------------------------------

class SendSingleReminderView(TenantRequiredMixin, View):
    """
    Send a WhatsApp reminder for a specific Udhaar/Collection record.
    Supports template selection and custom message preview.
    """
    def post(self, request, pk):
        u = get_object_or_404(Udhaar, pk=pk, business=request.business)
        business = request.business
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        template_id = request.POST.get('template_id')
        custom_msg = request.POST.get('custom_message', '').strip()

        # Build message
        if custom_msg:
            msg_body = custom_msg
        elif template_id:
            tmpl = WhatsAppMessageTemplate.objects.filter(pk=template_id, business=business).first()
            if tmpl:
                msg_body = (tmpl.content
                    .replace('{{customer_name}}', u.customer.name)
                    .replace('{{amount}}', f'₹{u.remaining_amount:,.0f}')
                    .replace('{{invoice_number}}', u.sale.invoice_number if u.sale else 'N/A')
                    .replace('{{due_date}}', u.due_date.strftime('%d %b %Y') if u.due_date else '')
                    .replace('{{days_overdue}}', str(u.days_overdue))
                )
            else:
                msg_body = f"Namaste {u.customer.name} ji, ₹{u.remaining_amount:,.0f} ka payment pending hai. Kripya payment karein."
        else:
            if u.days_overdue > 0:
                msg_body = f"Namaste {u.customer.name} ji, aapka ₹{u.remaining_amount:,.0f} ka payment {u.days_overdue} din se overdue hai. Kripya jald se payment karein."
            elif u.due_date and u.due_date == timezone.now().date():
                msg_body = f"Namaste {u.customer.name} ji, aaj aapke ₹{u.remaining_amount:,.0f} ka payment due hai."
            else:
                msg_body = f"Namaste {u.customer.name} ji, ₹{u.remaining_amount:,.0f} ka payment {u.due_date.strftime('%d %b %Y') if u.due_date else 'soon'} tak due hai."

        conv, _ = WhatsAppConversation.objects.get_or_create(business=business, customer=u.customer)
        WhatsAppMessage.objects.create(
            conversation=conv,
            sender='business',
            message_text=msg_body,
            status='Sent'
        )
        u.last_reminder_sent = timezone.now()
        u.save(update_fields=['last_reminder_sent'])

        CollectionActivity.objects.create(
            business=business,
            udhaar=u,
            activity_type='reminder_sent',
            description=f"WhatsApp reminder sent: {msg_body[:80]}",
            performed_by=request.user.username
        )

        if is_ajax:
            return JsonResponse({'status': 'success', 'message': f'Reminder sent to {u.customer.name}!'})

        messages.success(request, f"✅ WhatsApp reminder sent to {u.customer.name}!")
        return redirect('collections:list')


# ---------------------------------------------------------------------------
# Promise to Pay Views
# ---------------------------------------------------------------------------

class SetPromiseView(TenantRequiredMixin, View):
    """
    Set a payment promise for a collection record.
    """
    def post(self, request, pk):
        u = get_object_or_404(Udhaar, pk=pk, business=request.business)
        promised_date_str = request.POST.get('promised_date')
        promised_amount_str = request.POST.get('promised_amount', '')
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        try:
            promised_date = datetime.datetime.strptime(promised_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': 'Invalid date.'}, status=400)
            messages.error(request, "Invalid date provided.")
            return redirect('collections:list')

        try:
            promised_amount = float(promised_amount_str) if promised_amount_str else float(u.remaining_amount)
        except ValueError:
            promised_amount = float(u.remaining_amount)

        u.promised_date = promised_date
        u.promised_amount = promised_amount
        u.promise_broken = False
        u.status = 'Payment Promised'
        u.save()

        CollectionActivity.objects.create(
            business=request.business,
            udhaar=u,
            activity_type='promise_made',
            description=f"Payment promise set: ₹{promised_amount:,.0f} by {promised_date.strftime('%d %b %Y')}",
            amount=promised_amount,
            performed_by=request.user.username
        )

        if is_ajax:
            return JsonResponse({
                'status': 'success',
                'message': f'Promise recorded: ₹{promised_amount:,.0f} by {promised_date.strftime("%d %b %Y")}',
                'promised_date': promised_date.strftime('%d %b %Y'),
                'promised_amount': float(promised_amount),
            })

        messages.success(request, f"✅ Payment promise set: ₹{promised_amount:,.0f} by {promised_date.strftime('%d %b %Y')}")
        return redirect('udhaar:detail', pk=u.pk)


# ---------------------------------------------------------------------------
# Collection Reports View
# ---------------------------------------------------------------------------

class CollectionReportsView(TenantRequiredMixin, View):
    template_name = 'collections/reports.html'

    def get(self, request):
        import json
        business = request.business
        today = timezone.now().date()
        first_of_month = today.replace(day=1)

        all_udhaars = Udhaar.objects.filter(business=business)
        active = all_udhaars.exclude(status='Paid')

        # Aging buckets
        aging = {
            '0_30': active.filter(due_date__gte=today - datetime.timedelta(days=30), due_date__lte=today).aggregate(s=Sum('remaining_amount'))['s'] or 0,
            '31_60': active.filter(due_date__lt=today - datetime.timedelta(days=30), due_date__gte=today - datetime.timedelta(days=60)).aggregate(s=Sum('remaining_amount'))['s'] or 0,
            '61_90': active.filter(due_date__lt=today - datetime.timedelta(days=60), due_date__gte=today - datetime.timedelta(days=90)).aggregate(s=Sum('remaining_amount'))['s'] or 0,
            '90_plus': active.filter(due_date__lt=today - datetime.timedelta(days=90)).aggregate(s=Sum('remaining_amount'))['s'] or 0,
        }

        # Collection stats
        total_billed = all_udhaars.aggregate(s=Sum('total_amount'))['s'] or 0
        total_collected = all_udhaars.aggregate(s=Sum('paid_amount'))['s'] or 0
        total_outstanding = active.aggregate(s=Sum('remaining_amount'))['s'] or 0
        collection_rate = round((float(total_collected) / float(total_billed) * 100), 1) if total_billed else 0

        # Monthly collection trend (last 6 months)
        monthly_labels = []
        monthly_collected = []
        monthly_outstanding = []
        for i in range(5, -1, -1):
            month_start = (today.replace(day=1) - datetime.timedelta(days=i * 30)).replace(day=1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - datetime.timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1) - datetime.timedelta(days=1)

            collected = Payment.objects.filter(
                business=business,
                created_at__date__gte=month_start,
                created_at__date__lte=month_end
            ).aggregate(s=Sum('amount'))['s'] or 0

            outstanding = all_udhaars.filter(
                created_at__date__lte=month_end
            ).exclude(status='Paid').aggregate(s=Sum('remaining_amount'))['s'] or 0

            monthly_labels.append(month_start.strftime('%b %Y'))
            monthly_collected.append(float(collected))
            monthly_outstanding.append(float(outstanding))

        # Top overdue customers
        top_overdue = (
            active.filter(due_date__lt=today)
            .values('customer__name', 'customer__phone')
            .annotate(total_overdue=Sum('remaining_amount'))
            .order_by('-total_overdue')[:10]
        )

        # Promise stats
        promises_kept = all_udhaars.filter(status='Paid', promised_date__isnull=False).count()
        promises_missed = all_udhaars.filter(promise_broken=True).count()
        promises_active = all_udhaars.filter(status='Payment Promised').count()

        # Avg payment delay
        paid_with_dates = all_udhaars.filter(status='Paid', due_date__isnull=False)
        delay_sum = 0
        delay_count = 0
        for u in paid_with_dates[:100]:  # sample
            last_pay = Payment.objects.filter(udhaar=u).order_by('-created_at').first()
            if last_pay:
                delay = (last_pay.created_at.date() - u.due_date).days
                if delay > 0:
                    delay_sum += delay
                    delay_count += 1
        avg_delay = round(delay_sum / delay_count, 1) if delay_count else 0

        context = {
            'today': today,
            'aging': aging,
            'total_billed': total_billed,
            'total_collected': total_collected,
            'total_outstanding': total_outstanding,
            'collection_rate': collection_rate,
            'avg_delay': avg_delay,
            'top_overdue': list(top_overdue),
            'promises_kept': promises_kept,
            'promises_missed': promises_missed,
            'promises_active': promises_active,
            'monthly_labels': json.dumps(monthly_labels),
            'monthly_collected': json.dumps(monthly_collected),
            'monthly_outstanding': json.dumps(monthly_outstanding),
            'aging_labels': json.dumps(['0–30 days', '31–60 days', '61–90 days', '90+ days']),
            'aging_data': json.dumps([float(aging['0_30']), float(aging['31_60']), float(aging['61_90']), float(aging['90_plus'])]),
        }
        return render(request, self.template_name, context)


# ---------------------------------------------------------------------------
# Reminder Rules View
# ---------------------------------------------------------------------------

class ReminderRulesView(TenantRequiredMixin, View):
    template_name = 'collections/reminder_rules.html'

    def get(self, request):
        business = request.business
        rules = ReminderRule.objects.filter(business=business)
        templates = WhatsAppMessageTemplate.objects.filter(business=business)

        # Create default rules if none exist
        if not rules.exists():
            defaults = [
                {'days_offset': -3, 'label': '3 days before due date', 'order': 1},
                {'days_offset': 0, 'label': 'On the due date', 'order': 2},
                {'days_offset': 3, 'label': '3 days overdue', 'order': 3},
                {'days_offset': 7, 'label': '7 days overdue', 'order': 4},
                {'days_offset': 15, 'label': '15 days overdue', 'order': 5},
                {'days_offset': 30, 'label': '30 days overdue', 'order': 6},
            ]
            for d in defaults:
                ReminderRule.objects.create(business=business, **d)
            rules = ReminderRule.objects.filter(business=business)

        return render(request, self.template_name, {
            'rules': rules,
            'templates': templates,
        })

    def post(self, request):
        business = request.business
        action = request.POST.get('action')

        if action == 'toggle':
            rule_id = request.POST.get('rule_id')
            rule = get_object_or_404(ReminderRule, pk=rule_id, business=business)
            rule.is_enabled = not rule.is_enabled
            rule.save()
            messages.success(request, f"Rule '{rule.label}' {'enabled' if rule.is_enabled else 'disabled'}.")

        elif action == 'add':
            days = request.POST.get('days_offset')
            label = request.POST.get('label', '').strip()
            template_id = request.POST.get('template_id')
            try:
                days_int = int(days)
                tmpl = WhatsAppMessageTemplate.objects.filter(pk=template_id, business=business).first() if template_id else None
                ReminderRule.objects.create(
                    business=business,
                    days_offset=days_int,
                    label=label or f"{abs(days_int)} days {'before' if days_int < 0 else 'after'} due",
                    template=tmpl,
                    order=ReminderRule.objects.filter(business=business).count() + 1
                )
                messages.success(request, "Reminder rule added successfully.")
            except (ValueError, TypeError):
                messages.error(request, "Invalid days value.")

        elif action == 'delete':
            rule_id = request.POST.get('rule_id')
            ReminderRule.objects.filter(pk=rule_id, business=business).delete()
            messages.success(request, "Reminder rule deleted.")

        return redirect('collections:reminder_rules')


# ---------------------------------------------------------------------------
# Dashboard data API (JSON for AJAX refreshes)
# ---------------------------------------------------------------------------

class CollectionsDashboardDataView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        today = timezone.now().date()
        active = Udhaar.objects.filter(business=business).exclude(status='Paid')
        return JsonResponse({
            'total_outstanding': float(active.aggregate(s=Sum('remaining_amount'))['s'] or 0),
            'overdue': float(active.filter(due_date__lt=today).aggregate(s=Sum('remaining_amount'))['s'] or 0),
            'due_today': float(active.filter(due_date=today).aggregate(s=Sum('remaining_amount'))['s'] or 0),
            'upcoming': float(active.filter(due_date__gt=today).aggregate(s=Sum('remaining_amount'))['s'] or 0),
            'customers_needing_followup': active.filter(due_date__lte=today).values('customer').distinct().count(),
        })
