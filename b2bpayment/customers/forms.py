from django import forms
from .models import Customer
from whatsapp.models import Tag

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address', 'notes', 'status', 'credit_limit', 'referred_by', 'accepts_marketing', 'tags']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Ramesh Kumar'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'customer@example.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00 (0 = No limit)'}),
            'referred_by': forms.Select(attrs={'class': 'form-select'}),
            'accepts_marketing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
        }

    def __init__(self, *args, **kwargs):
        business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)
        if business:
            self.fields['referred_by'].queryset = Customer.objects.filter(business=business)
            self.fields['tags'].queryset = Tag.objects.filter(business=business)
            if self.instance and self.instance.pk:
                self.fields['referred_by'].queryset = self.fields['referred_by'].queryset.exclude(pk=self.instance.pk)
