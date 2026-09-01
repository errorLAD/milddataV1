from django import forms
from accounts.models import Business
from .models import BusinessSettings

class BusinessInfoForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'owner_name', 'phone', 'email', 'address', 'gstin']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'owner_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'gstin': forms.TextInput(attrs={'class': 'form-control'}),
        }

class RegionalSettingsForm(forms.ModelForm):
    class Meta:
        model = BusinessSettings
        fields = ['country', 'currency', 'currency_symbol', 'date_format', 'timezone', 'phone_code', 'tax_label', 'number_format']
        widgets = {
            'country': forms.Select(attrs={'class': 'form-select', 'id': 'countrySelect'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. USD, INR, GBP, EUR'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. $, ₹, £, €'}),
            'date_format': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MM/DD/YYYY or DD/MM/YYYY'}),
            'timezone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. America/New_York'}),
            'phone_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +1, +91, +44'}),
            'tax_label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Sales Tax, GST, VAT'}),
            'number_format': forms.Select(attrs={'class': 'form-select'}),
        }

class PaymentSettingsForm(forms.ModelForm):
    class Meta:
        model = BusinessSettings
        fields = ['currency', 'currency_symbol', 'upi_id', 'payee_name', 'payment_link', 'qr_code']
        widgets = {
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '₹ or $ or £ or €'}),
            'upi_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. sharma@upi'}),
            'payee_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Sharma Kirana'}),
            'payment_link': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://upiqr.in/pay/...'}),
            'qr_code': forms.FileInput(attrs={'class': 'form-control'}),
        }

class WhatsAppSettingsForm(forms.ModelForm):
    class Meta:
        model = BusinessSettings
        fields = ['whatsapp_phone_number_id', 'whatsapp_api_token']
        widgets = {
            'whatsapp_phone_number_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number ID'}),
            'whatsapp_api_token': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Permanent Access Token'}, render_value=True),
        }

class RecoveryRulesForm(forms.ModelForm):
    class Meta:
        model = BusinessSettings
        fields = ['reminder_before_due_days', 'reminder_on_due_date', 'followup_frequency_days', 'auto_send_payment_link', 'stop_reminders_on_payment']
        widgets = {
            'reminder_before_due_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'reminder_on_due_date': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'followup_frequency_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'auto_send_payment_link': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'stop_reminders_on_payment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class LateFeeSettingsForm(forms.ModelForm):
    class Meta:
        model = BusinessSettings
        fields = ['enable_late_fees', 'late_fee_type', 'late_fee_value', 'late_fee_grace_days', 'late_fee_frequency']
        widgets = {
            'enable_late_fees': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'late_fee_type': forms.Select(attrs={'class': 'form-select'}),
            'late_fee_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'late_fee_grace_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'late_fee_frequency': forms.Select(attrs={'class': 'form-select'}),
        }

class AISettingsForm(forms.ModelForm):
    class Meta:
        model = BusinessSettings
        fields = ['is_ai_enabled', 'ai_provider', 'ai_api_key', 'ai_model_name', 'ai_api_url', 'ai_temperature']
        widgets = {
            'is_ai_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ai_provider': forms.Select(attrs={'class': 'form-select', 'id': 'aiProviderSelect'}),
            'ai_api_key': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Paste Gemini or OpenAI API Key', 'id': 'aiApiKeyInput'}, render_value=True),
            'ai_model_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. gemini-1.5-flash or gpt-4o-mini'}),
            'ai_api_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional custom endpoint URL'}),
            'ai_temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.0', 'max': '1.0'}),
        }
