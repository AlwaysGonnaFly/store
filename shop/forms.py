from django import forms


class PurchaseForm(forms.Form):
    promo = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Промокод',
        'class': 'form-control',
    }), required=False, max_length=32)
    method = forms.CharField(widget=forms.HiddenInput(), required=True, max_length=32, initial='qiwi')
