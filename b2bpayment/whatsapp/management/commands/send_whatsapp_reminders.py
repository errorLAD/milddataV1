from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count
import datetime

from udhaar.models import Udhaar
from whatsapp.models import WhatsAppConversation, WhatsAppMessage, WhatsAppMessageTemplate
from settings_app.models import BusinessSettings
from notifications.models import Notification
from accounts.models import Business

class Command(BaseCommand):
    help = 'Scheduled command to check due dates, send automated WhatsApp reminders, track broken promises, calculate late fees, and notify owners.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        self.stdout.write(self.style.SUCCESS(f"Running automated Udhaar maintenance scan for date: {today}"))

        businesses = Business.objects.all()

        for b in businesses:
            settings_obj = BusinessSettings.objects.filter(business=b).first()

            # A. Check & Flag Broken Payment Promises
            broken_promises = Udhaar.objects.filter(
                business=b,
                promised_date__lt=today,
                promise_broken=False
            ).exclude(status='Paid')

            for u in broken_promises:
                u.promise_broken = True
                u.save()
                
                # Increment Customer broken promise counter
                c = u.customer
                c.promises_broken_count += 1
                c.save()

                Notification.objects.create(
                    business=b,
                    title=f"Broken Promise: {c.name}",
                    message=f"{c.name} failed to fulfill their promised payment of ₹{u.promised_amount or u.remaining_amount:,.2f} on {u.promised_date.strftime('%d %b %Y')}.",
                    category='Promise',
                    link=f'/udhaar/{u.pk}/'
                )

            # B. Apply Late Fees (if enabled in settings)
            if settings_obj and settings_obj.enable_late_fees:
                grace = settings_obj.late_fee_grace_days
                grace_date = today - datetime.timedelta(days=grace)

                overdue_for_fees = Udhaar.objects.filter(
                    business=b,
                    due_date__lt=grace_date,
                    late_fee_amount=0 # Apply one-time flat/percentage charge
                ).exclude(status__in=['Paid', 'Disputed'])

                for u in overdue_for_fees:
                    if settings_obj.late_fee_type == 'flat':
                        fee = settings_obj.late_fee_value
                    else:
                        fee = (u.remaining_amount * settings_obj.late_fee_value) / 100

                    u.late_fee_amount += fee
                    u.remaining_amount += fee
                    u.save()
                    self.stdout.write(self.style.SUCCESS(f"Applied ₹{fee} late fee to Udhaar #{u.pk} ({c.name})"))

            # C. Aggregated Due Today Notification for Business Owner
            due_today_qs = Udhaar.objects.filter(business=b, due_date=today).exclude(status='Paid')
            due_count = due_today_qs.count()
            if due_count > 0:
                due_total = due_today_qs.aggregate(s=Sum('remaining_amount'))['s'] or 0
                Notification.objects.create(
                    business=b,
                    title=f"Udhaar Due Today ({due_count} Accounts)",
                    message=f"{due_count} udhaar entries are due today totaling ₹{due_total:,.2f}.",
                    category='Udhaar Due Today',
                    link='/udhaar/?due=today'
                )

        # D. Automated WhatsApp Reminder Messages Dispatch
        active_udhaars = Udhaar.objects.exclude(status__in=['Paid', 'Disputed'])
        reminders_sent = 0

        for u in active_udhaars:
            business = u.business
            settings_obj = BusinessSettings.objects.filter(business=business).first()

            conv, _ = WhatsAppConversation.objects.get_or_create(business=business, customer=u.customer)
            if conv.is_human_takeover:
                continue

            days_before = settings_obj.reminder_before_due_days if settings_obj else 2
            due_minus_n = u.due_date - datetime.timedelta(days=days_before)

            should_send = False
            msg_type = 'Due Reminder'

            if today == due_minus_n and (not u.last_reminder_sent or u.last_reminder_sent.date() < today):
                should_send = True
                msg_type = 'Due Reminder'
            elif today == u.due_date and (not u.last_reminder_sent or u.last_reminder_sent.date() < today):
                should_send = True
                msg_type = 'Due Reminder'
            elif today > u.due_date:
                freq = settings_obj.followup_frequency_days if settings_obj else 3
                if not u.last_reminder_sent or (today - u.last_reminder_sent.date()).days >= freq:
                    should_send = True
                    msg_type = 'Overdue Reminder'

            if should_send:
                tpl = WhatsAppMessageTemplate.objects.filter(business=business, trigger_type=msg_type).first()
                upi = settings_obj.upi_id if settings_obj and settings_obj.upi_id else "Business UPI"
                link = settings_obj.payment_link if settings_obj and settings_obj.payment_link else ""

                if tpl:
                    body = tpl.content.replace('{{customer_name}}', u.customer.name)\
                                       .replace('{{business_name}}', business.name)\
                                       .replace('{{amount}}', f"₹{u.remaining_amount:,.2f}")\
                                       .replace('{{due_date}}', u.due_date.strftime('%d %b %Y'))\
                                       .replace('{{upi_id}}', upi)\
                                       .replace('{{payment_link}}', link)
                else:
                    body = f"Namaste {u.customer.name}, {business.name} se aapka Udhaar balance ₹{u.remaining_amount:,.2f} pending hai (Due: {u.due_date.strftime('%d %b %Y')}). UPI: {upi}"

                WhatsAppMessage.objects.create(
                    conversation=conv,
                    sender='system',
                    message_text=body,
                    status='Sent'
                )

                u.last_reminder_sent = timezone.now()
                if u.is_overdue and u.status != 'Overdue':
                    u.status = 'Overdue'
                u.save()

                reminders_sent += 1

        self.stdout.write(self.style.SUCCESS(f"Maintenance scan finished! Reminders sent: {reminders_sent}"))
