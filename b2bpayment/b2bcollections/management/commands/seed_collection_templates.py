"""
Seed default WhatsApp message templates for B2B Payment Collections.
Run once after setup:
  python manage.py seed_collection_templates
"""
from django.core.management.base import BaseCommand
from accounts.models import Business
from whatsapp.models import WhatsAppMessageTemplate


TEMPLATES = [
    # --- Due Reminder ---
    {
        'trigger_type': 'Due Reminder',
        'title': 'Friendly Due Reminder (English)',
        'content': (
            "Hello {{customer_name}}, this is a reminder that your payment of ₹{{amount}} "
            "is due on {{due_date}}. Please arrange the payment at your earliest convenience. "
            "Thank you for your business! 🙏"
        ),
    },
    {
        'trigger_type': 'Due Reminder',
        'title': 'Due Reminder — Hindi/Hinglish',
        'content': (
            "Namaste {{customer_name}} ji 🙏\n"
            "Aapka ₹{{amount}} ka payment {{due_date}} ko due hai.\n"
            "Kripya samay par payment karein. Dhanyawad!"
        ),
    },
    # --- Overdue Reminder ---
    {
        'trigger_type': 'Overdue Reminder',
        'title': 'Overdue Reminder — Friendly (English)',
        'content': (
            "Hello {{customer_name}}, your payment of ₹{{amount}} "
            "against invoice #{{invoice_number}} is currently {{days_overdue}} days overdue. "
            "Please let us know your expected payment date. Thank you."
        ),
    },
    {
        'trigger_type': 'Overdue Reminder',
        'title': 'Overdue Reminder — Professional (English)',
        'content': (
            "Payment Reminder: Dear {{customer_name}}, ₹{{amount}} against invoice #{{invoice_number}} "
            "is {{days_overdue}} days past due. Kindly arrange payment immediately or contact us "
            "to discuss a payment plan. This is an automated reminder."
        ),
    },
    {
        'trigger_type': 'Overdue Reminder',
        'title': 'Overdue Reminder — Hindi/Hinglish',
        'content': (
            "Namaste {{customer_name}} ji 🙏\n"
            "₹{{amount}} ka payment {{days_overdue}} din se overdue hai.\n"
            "Invoice #{{invoice_number}}\n"
            "Kripya jald se jald payment karein ya payment ki expected date bata dein.\n"
            "Dhanyawad!"
        ),
    },
    # --- Promise Confirmation ---
    {
        'trigger_type': 'Promise Confirmation',
        'title': 'Promise Confirmation (English)',
        'content': (
            "Thank you {{customer_name}}! We've noted your payment commitment of ₹{{amount}}. "
            "We look forward to receiving your payment on the agreed date. "
            "If you have any questions, please don't hesitate to contact us."
        ),
    },
    {
        'trigger_type': 'Promise Confirmation',
        'title': 'Promise Confirmation — Hindi',
        'content': (
            "Dhanyawad {{customer_name}} ji! 🙏\n"
            "Humne aapka ₹{{amount}} ka payment commitment note kar liya hai.\n"
            "Koi bhi samasya ho toh hume batayein."
        ),
    },
    # --- Payment Received ---
    {
        'trigger_type': 'Payment Received',
        'title': 'Payment Received Confirmation (English)',
        'content': (
            "Dear {{customer_name}}, we have received your payment of ₹{{amount}}. "
            "Thank you! Your account has been updated. "
            "We appreciate your prompt payment. 🙏"
        ),
    },
    {
        'trigger_type': 'Payment Received',
        'title': 'Payment Received — Hindi',
        'content': (
            "Dhanyawad {{customer_name}} ji! 🙏\n"
            "Aapka ₹{{amount}} ka payment mil gaya hai.\n"
            "Aapka account update ho gaya hai. Bahut bahut shukriya!"
        ),
    },
]


class Command(BaseCommand):
    help = 'Seed default WhatsApp message templates for B2B Payment Collections'

    def handle(self, *args, **options):
        businesses = Business.objects.filter(is_active=True)

        if not businesses.exists():
            self.stdout.write(self.style.WARNING('No active businesses found. Run after creating a business.'))
            return

        for business in businesses:
            created_count = 0
            for tmpl_data in TEMPLATES:
                _, created = WhatsAppMessageTemplate.objects.get_or_create(
                    business=business,
                    title=tmpl_data['title'],
                    defaults={
                        'trigger_type': tmpl_data['trigger_type'],
                        'content': tmpl_data['content'],
                    }
                )
                if created:
                    created_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {business.name}: Created {created_count} new templates '
                    f'({len(TEMPLATES) - created_count} already existed)'
                )
            )

        self.stdout.write(self.style.SUCCESS('\nTemplate seeding complete!'))
        self.stdout.write(
            'Variables available in templates: {{customer_name}}, {{amount}}, '
            '{{invoice_number}}, {{due_date}}, {{days_overdue}}'
        )
