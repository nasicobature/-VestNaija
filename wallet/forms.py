from django import forms


class DepositForm(forms.Form):
    amount = forms.DecimalField(min_value=5000, max_digits=18, decimal_places=2)


class WithdrawalForm(forms.Form):
    amount = forms.DecimalField(min_value=1000, max_digits=18, decimal_places=2)
    bank = forms.CharField(max_length=120)
    account_number = forms.CharField(max_length=20, min_length=10)
    account_name = forms.CharField(max_length=160)
