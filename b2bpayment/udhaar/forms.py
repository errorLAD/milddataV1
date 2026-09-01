from django import forms
from .models import Udhaar
from customers.models import Customer

class UdhaarForm(forms.ModelForm):
    class Meta:
        model = Udhaar
        fields = ['customer', 'total_amount', 'due_date', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)
        if business:
            self.fields['customer'].queryset = Customer.objects.filter(business=business)

class PartialPaymentForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Payment amount (₹)'})
    )
    payment_method = forms.ChoiceField(
        choices=[('UPI', 'UPI'), ('Cash', 'Cash'), ('Bank Transfer', 'Bank Transfer'), ('Online', 'Online Payment')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reference_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transaction Ref / UTR #'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional payment note'})
    )

class ChangeDueDateForm(forms.Form):
    new_due_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class PromiseForm(forms.Form):
    promised_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    promised_amount = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Promised amount'})
    )
