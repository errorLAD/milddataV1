from django.db import models
from core.models import TenantModel

from core.localization import get_country_choices, get_country_profile

class BusinessSettings(TenantModel):
    # Country-Based Regional Configuration
    country = models.CharField(max_length=10, default='US', choices=get_country_choices(), verbose_name="Business Country")
    currency = models.CharField(max_length=10, default='USD', verbose_name="Currency Code")
    currency_symbol = models.CharField(max_length=5, default='$', verbose_name="Currency Symbol")
    date_format = models.CharField(max_length=20, default='MM/DD/YYYY', verbose_name="Date Format")
    timezone = models.CharField(max_length=50, default='America/New_York', verbose_name="Timezone")
    phone_code = models.CharField(max_length=10, default='+1', verbose_name="Phone Country Code")
    tax_label = models.CharField(max_length=20, default='Sales Tax', verbose_name="Tax Label")
    number_format = models.CharField(max_length=20, default='standard', choices=(('standard', 'Standard (149,999)'), ('indian', 'Indian (1,49,999)')), verbose_name="Number Formatting")

    def apply_country_defaults(self, country_code):
        profile = get_country_profile(country_code)
        self.country = profile['code']
        self.currency = profile['currency']
        self.currency_symbol = profile['symbol']
        self.date_format = profile['date_format']
        self.timezone = profile['timezone']
        self.phone_code = profile['phone_code']
        self.tax_label = profile['tax_label']
        self.number_format = profile['number_format']

    # Payment Settings
    upi_id = models.CharField(max_length=100, blank=True, verbose_name="UPI ID (e.g. 9876543210@upi)")
    payee_name = models.CharField(max_length=255, blank=True, verbose_name="Payee / Merchant Name")
    payment_link = models.CharField(max_length=500, blank=True, verbose_name="Static Payment Link / Razorpay / PhonePe Link")
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name="UPI QR Code Image")

    # WhatsApp API Credentials
    whatsapp_phone_number_id = models.CharField(max_length=100, blank=True)
    whatsapp_api_token = models.CharField(max_length=500, blank=True)

    # Automatic Recovery Rules
    reminder_before_due_days = models.IntegerField(default=2, verbose_name="Send reminder N days before due date")
    reminder_on_due_date = models.BooleanField(default=True, verbose_name="Send reminder on exact due date")
    followup_frequency_days = models.IntegerField(default=3, verbose_name="Follow-up frequency after overdue (days)")
    auto_send_payment_link = models.BooleanField(default=True, verbose_name="Auto-send UPI link when customer asks 'UPI bhejo'")
    stop_reminders_on_payment = models.BooleanField(default=True, verbose_name="Stop automated reminders once payment is recorded")

    # Interest / Late Fee Rules
    LATE_FEE_TYPE_CHOICES = (
        ('flat', 'Flat Amount (₹)'),
        ('percent', 'Percentage of Outstanding (%)'),
    )
    LATE_FEE_FREQ_CHOICES = (
        ('one_time', 'One-Time Charge'),
        ('recurring', 'Recurring (Every 30 Days Overdue)'),
    )
    enable_late_fees = models.BooleanField(default=False, verbose_name="Enable Late Fees / Interest on Overdue Udhaar")
    late_fee_type = models.CharField(max_length=20, choices=LATE_FEE_TYPE_CHOICES, default='flat')
    late_fee_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Late Fee Amount or Percent")
    late_fee_grace_days = models.IntegerField(default=5, verbose_name="Grace Period (Days past due date)")
    late_fee_frequency = models.CharField(max_length=20, choices=LATE_FEE_FREQ_CHOICES, default='one_time')

    # AI API Credentials & Provider Settings
    AI_PROVIDER_CHOICES = (
        ('gemini', 'Google Gemini AI'),
        ('openai', 'OpenAI ChatGPT'),
        ('custom_llm', 'Custom OpenAI-Compatible API'),
        ('rule_based', 'Built-in Analytics Engine (No API Key Required)'),
    )
    ai_provider = models.CharField(max_length=50, choices=AI_PROVIDER_CHOICES, default='gemini', verbose_name="AI Provider")
    ai_api_key = models.CharField(max_length=255, blank=True, verbose_name="AI API Key")
    ai_model_name = models.CharField(max_length=100, default='gemini-1.5-flash', verbose_name="AI Model Name (e.g. gemini-1.5-flash, gpt-4o-mini)")
    ai_api_url = models.CharField(max_length=255, blank=True, verbose_name="Custom API Endpoint URL")
    ai_temperature = models.FloatField(default=0.2, verbose_name="AI Temperature")
    is_ai_enabled = models.BooleanField(default=True, verbose_name="Enable AI Features")

    def __str__(self):
        return f"Settings for {self.business.name}"
