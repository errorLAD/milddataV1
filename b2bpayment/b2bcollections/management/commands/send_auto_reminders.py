"""
Django management command: send_auto_reminders

Sends automatic WhatsApp reminders based on each business's ReminderRule configuration.
Run daily via cron or Windows Task Scheduler:

  python manage.py send_auto_reminders

Or for a specific business only:

  python manage.py send_auto_reminders --business-id 1
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from accounts.models import Business
from udhaar.models import Udhaar
from whatsapp.models import WhatsAppConversation, WhatsAppMessage
from collections.models import ReminderRule, CollectionActivity


class Command(BaseCommand):
    help = 'Send automatic WhatsApp payment reminders based on configured reminder rules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--business-id',
            type=int,
            help='Only process a specific business ID (default: all active businesses)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        dry_run = options.get('dry_run', False)
        business_id = options.get('business_id')

        businesses = Business.objects.filter(is_active=True)
        if business_id:
            businesses = businesses.filter(pk=business_id)

        total_sent = 0
        total_skipped = 0

        self.stdout.write(self.style.SUCCESS(
            f"\n{'[DRY RUN] ' if dry_run else ''}Starting auto-reminders for {businesses.count()} business(es) — {today}\n"
        ))

        for business in businesses:
            rules = ReminderRule.objects.filter(business=business, is_enabled=True)

            if not rules.exists():
                self.stdout.write(f"  ⚠ {business.name}: No reminder rules configured, skipping.")
                continue

            self.stdout.write(f"\n📋 {business.name} ({rules.count()} active rules):")

            for rule in rules:
                # Determine target date for this rule
                target_date = today - timezone.timedelta(days=rule.days_offset)
                # rule.days_offset: -3 = "3 days before due" → target_date = today + 3 days = due_date
                # rule.days_offset: +7 = "7 days overdue" → target_date = today - 7 = due_date

                # Find all active Udhaar records where due_date matches target_date
                udhaars = Udhaar.objects.filter(
                    business=business,
                    due_date=target_date
                ).exclude(status='Paid').select_related('customer')

                self.stdout.write(
                    f"  Rule: '{rule.label}' → targeting due_date={target_date} → {udhaars.count()} record(s)"
                )

                for u in udhaars:
                    # Skip if reminder sent within last 20 hours (anti-spam)
                    if u.last_reminder_sent:
                        hours_since = (timezone.now() - u.last_reminder_sent).total_seconds() / 3600
                        if hours_since < 20:
                            self.stdout.write(
                                f"    ⏭ Skipped {u.customer.name} — reminder sent {hours_since:.0f}h ago"
                            )
                            total_skipped += 1
                            continue

                    # Build message from template or default
                    if rule.template:
                        msg = (rule.template.content
                               .replace('{{customer_name}}', u.customer.name)
                               .replace('{{amount}}', f'₹{u.remaining_amount:,.0f}')
                               .replace('{{invoice_number}}', u.sale.invoice_number if u.sale else 'N/A')
                               .replace('{{due_date}}', u.due_date.strftime('%d %b %Y') if u.due_date else '')
                               .replace('{{days_overdue}}', str(u.days_overdue))
                               )
                    elif rule.days_offset < 0:
                        days_before = abs(rule.days_offset)
                        msg = (
                            f"Namaste {u.customer.name} ji, {business.name} ki taraf se yaad dilaana chahte hain "
                            f"ki ₹{u.remaining_amount:,.0f} ka payment agle {days_before} din mein due hai "
                            f"({u.due_date.strftime('%d %b %Y')}). Dhanyawad!"
                        )
                    elif rule.days_offset == 0:
                        msg = (
                            f"Namaste {u.customer.name} ji, aaj {business.name} ka ₹{u.remaining_amount:,.0f} "
                            f"ka payment due hai. Kripya aaj payment karein. Dhanyawad!"
                        )
                    else:
                        msg = (
                            f"Namaste {u.customer.name} ji, aapka {business.name} ka ₹{u.remaining_amount:,.0f} "
                            f"ka payment {u.days_overdue} din se overdue hai. Kripya turant payment karein. Dhanyawad!"
                        )

                    if not dry_run:
                        conv, _ = WhatsAppConversation.objects.get_or_create(
                            business=business,
                            customer=u.customer
                        )
                        WhatsAppMessage.objects.create(
                            conversation=conv,
                            sender='system',
                            message_text=msg,
                            status='Sent'
                        )
                        u.last_reminder_sent = timezone.now()
                        u.save(update_fields=['last_reminder_sent'])

                        CollectionActivity.objects.create(
                            business=business,
                            udhaar=u,
                            activity_type='reminder_sent',
                            description=f"Auto-reminder sent ({rule.label}): {msg[:60]}...",
                            performed_by='System Auto'
                        )

                    self.stdout.write(
                        f"    {'[DRY] ' if dry_run else ''}✅ Sent to {u.customer.name} ({u.customer.phone}) — ₹{u.remaining_amount:,.0f}"
                    )
                    total_sent += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'[DRY RUN] ' if dry_run else ''}Done! Sent: {total_sent}, Skipped: {total_skipped}\n"
            )
        )
