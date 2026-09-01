from django import forms
from .models import SalesAgentSettings
from products.models import Product
from whatsapp.models import WhatsAppMessageTemplate
from customers.models import Customer

class PDFUploadForm(forms.Form):
    pdf_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        label="Upload Customer List PDF"
    )

class SalesBlastForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Product to Blast"
    )
    template = forms.ModelChoiceField(
        queryset=WhatsAppMessageTemplate.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Sales Blast Template"
    )
    custom_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional custom message (overrides template). Supports {name}, {product}, {price}.'}),
        label="Custom Blast Message (Optional)"
    )

    def __init__(self, *args, **kwargs):
        business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)
        if business:
            self.fields['product'].queryset = Product.objects.filter(business=business)
            self.fields['template'].queryset = WhatsAppMessageTemplate.objects.filter(business=business, trigger_type='Sales Blast')

class SalesAgentSettingsForm(forms.ModelForm):
    class Meta:
        model = SalesAgentSettings
        fields = ['is_enabled', 'auto_draft_orders', 'greeting_message', 'anti_spam_window_hours']
        widgets = {
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_draft_orders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'greeting_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'anti_spam_window_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
