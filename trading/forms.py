from django import forms

from .models import Order


class OrderForm(forms.Form):
    side = forms.ChoiceField(choices=Order.Side.choices)
    order_type = forms.ChoiceField(choices=Order.OrderType.choices)
    quantity = forms.IntegerField(min_value=1)
    limit_price = forms.DecimalField(max_digits=18, decimal_places=2, required=False, min_value=0)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("order_type") == Order.OrderType.LIMIT and not cleaned.get("limit_price"):
            raise forms.ValidationError("Limit price is required for limit orders.")
        return cleaned
