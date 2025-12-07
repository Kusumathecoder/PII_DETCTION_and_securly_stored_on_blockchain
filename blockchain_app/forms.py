from django import forms

class TransactionForm(forms.Form):
    transaction_id = forms.CharField(
        max_length=64,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Hash'
        })
    )
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Name'
        })
    )
