from django import template
from decimal import Decimal
import datetime

register = template.Library()

@register.filter(name='money')
def money_format(value, org=None):
    if value is None or value == '':
        value = 0
    try:
        val = Decimal(str(value))
    except Exception:
        val = Decimal('0.00')

    # Get settings from org or default
    decimals = getattr(org, 'decimal_places', 2) if org else 2
    symbol = getattr(org, 'currency_symbol', '$') if org else '$'
    position = getattr(org, 'currency_position', 'prefix') if org else 'prefix'
    num_fmt = getattr(org, 'number_format', '1,234.56') if org else '1,234.56'

    # Format numeric value
    formatted_val = f"{val:,.{decimals}f}"

    if num_fmt == '1.234,56':
        # European format: 1.234,56
        formatted_val = formatted_val.replace(',', 'X').replace('.', ',').replace('X', '.')
    elif num_fmt == '1 234,56':
        # Space separator: 1 234,56
        formatted_val = formatted_val.replace(',', ' ').replace('.', ',')

    if position == 'suffix':
        return f"{formatted_val} {symbol}"
    return f"{symbol}{formatted_val}"

@register.filter(name='number_fmt')
def number_format(value, org=None):
    if value is None or value == '':
        return '0'
    try:
        val = float(value)
    except Exception:
        return str(value)

    num_fmt = getattr(org, 'number_format', '1,234.56') if org else '1,234.56'
    formatted_val = f"{val:,.2f}".rstrip('0').rstrip('.')

    if num_fmt == '1.234,56':
        formatted_val = formatted_val.replace(',', 'X').replace('.', ',').replace('X', '.')
    elif num_fmt == '1 234,56':
        formatted_val = formatted_val.replace(',', ' ').replace('.', ',')

    return formatted_val

@register.filter(name='date_fmt')
def date_format(value, org=None):
    if not value:
        return ''
    
    if isinstance(value, str):
        try:
            value = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return value

    fmt_setting = getattr(org, 'date_format', 'MM/DD/YYYY') if org else 'MM/DD/YYYY'

    if fmt_setting == 'DD/MM/YYYY':
        return value.strftime('%d/%m/%Y')
    elif fmt_setting == 'DD.MM.YYYY':
        return value.strftime('%d.%m.%Y')
    elif fmt_setting == 'YYYY-MM-DD':
        return value.strftime('%Y-%m-%d')
    else: # MM/DD/YYYY
        return value.strftime('%m/%d/%Y')

@register.simple_tag
def tax_name(org=None):
    return getattr(org, 'tax_name', 'Tax') if org else 'Tax'

@register.simple_tag
def tax_id_label(org=None):
    return getattr(org, 'tax_id_label', 'Tax ID') if org else 'Tax ID'
