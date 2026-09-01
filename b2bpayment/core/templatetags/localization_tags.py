from django import template
from core.localization import format_money

register = template.Library()

@register.filter(name='money')
def money_filter(value, symbol_or_context=None):
    """
    Format money using symbol from arg, context, or fallback.
    Usage: {{ amount|money }} or {{ amount|money:"$" }} or {{ amount|money:business_currency_symbol }}
    """
    sym = symbol_or_context if symbol_or_context else '$'
    return format_money(value, symbol=sym)


@register.filter(name='money_record')
def money_record_filter(value, record):
    """
    Format money for a specific historical record (Udhaar, Sale, Payment),
    using the currency_symbol saved directly on that record.
    """
    sym = getattr(record, 'currency_symbol', '$')
    return format_money(value, symbol=sym)


@register.filter(name='country_flag')
def country_flag_filter(country_code):
    from core.localization import get_country_profile
    return get_country_profile(country_code).get('flag', '🌐')


@register.filter(name='tax_label')
def tax_label_filter(value, default_label='Sales Tax'):
    return value if value else default_label
