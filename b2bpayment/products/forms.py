from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'barcode', 'category', 'selling_price', 'cost_price', 'stock_quantity', 'low_stock_threshold']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Fortune Mustard Oil 1L'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SK-OIL-101'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 8901234567890'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Grocery / Edible Oils'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '180.00'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '155.00'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5'}),
        }
