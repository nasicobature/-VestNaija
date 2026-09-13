from django import template

register = template.Library()


@register.filter
def naira(value):
    try:
        return f"NGN {value:,.2f}"
    except (TypeError, ValueError):
        return "NGN 0.00"
