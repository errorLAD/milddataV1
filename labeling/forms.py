from django import forms

from .models import QuoteRequest


class QuoteRequestForm(forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = [
            "company_name",
            "email",
            "data_type",
            "volume",
            "timeline",
            "message",
        ]
        widgets = {
            "company_name": forms.TextInput(
                attrs={"placeholder": "Your company name"}
            ),
            "email": forms.EmailInput(
                attrs={"placeholder": "you@company.com"}
            ),
            "data_type": forms.Select(),
            "volume": forms.TextInput(
                attrs={"placeholder": "e.g. 500 hours of audio"}
            ),
            "timeline": forms.TextInput(
                attrs={"placeholder": "e.g. 4 weeks"}
            ),
            "message": forms.Textarea(
                attrs={
                    "placeholder": "Tell us about your project requirements...",
                    "rows": 4,
                }
            ),
        }
