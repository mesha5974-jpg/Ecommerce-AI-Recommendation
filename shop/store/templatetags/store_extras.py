from decimal import Decimal, InvalidOperation

from django import template
from django.conf import settings

register = template.Library()


@register.filter
def money(value):
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return ""
    return f"{settings.CURRENCY_SYMBOL}{amount:,.2f}"


@register.filter
def stars(value):
    """Return a list of 'full' / 'half' / 'empty' for a 0-5 rating."""
    try:
        rating = float(value or 0)
    except (TypeError, ValueError):
        rating = 0
    out = []
    for i in range(1, 6):
        if rating >= i - 0.25:
            out.append("full")
        elif rating >= i - 0.75:
            out.append("half")
        else:
            out.append("empty")
    return out


@register.filter
def in_set(value, container):
    return value in container


@register.simple_tag(takes_context=True)
def query_without(context, *keys, **extra):
    """Current query string with some keys removed (and extras set); used for filter chips & pagination."""
    params = context["request"].GET.copy()
    for key in keys:
        params.pop(key, None)
    for key, val in extra.items():
        params[key] = val
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else "?"


@register.simple_tag(takes_context=True)
def query_remove_value(context, key, value):
    params = context["request"].GET.copy()
    values = [v for v in params.getlist(key) if v != str(value)]
    params.setlist(key, values)
    params.pop("page", None)
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else "?"
