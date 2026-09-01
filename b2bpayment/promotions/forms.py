from django import forms
from .models import Promotion, PromotionImage

class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['name', 'title', 'message', 'start_date', 'end_date', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Diwali Festival Sale 2026'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 🎉 Diwali Special 10% OFF Offer'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '🎉 Diwali Special Offer\nGet 10% OFF on selected hardware products.\nOffer valid until 30 August.\nContact us to order.'
            }),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class PromotionImageForm(forms.ModelForm):
    class Meta:
        model = PromotionImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
