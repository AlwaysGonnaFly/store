from django import forms
from django.core.exceptions import ValidationError

from .models import User


class UserAuthForm(forms.ModelForm):
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={
        'placeholder': 'Введите email',
        'class': 'form-control'
    }))

    class Meta:
        model = User
        fields = ('email',)


class DepositForm(forms.Form):
    amount = forms.IntegerField(widget=forms.NumberInput(attrs={
        'placeholder': 'Сумма',
        'class': 'form-control',
    }), required=True)
    method = forms.CharField(widget=forms.HiddenInput(), required=True, max_length=32, initial='qiwi')

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if 100 <= amount <= 100000:
            return amount
        return ValidationError('Минимальная сумма пополнения - 100 рублей.')
