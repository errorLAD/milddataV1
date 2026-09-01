from django import template
import math

register = template.Library()

@register.filter(name='inr')
@register.filter(name='money')
def inr_currency(value, symbol='₹'):
    """
    Format monetary amounts dynamically according to currency symbol ($ USD, ₹ INR, £ GBP, € EUR).
    """
    if value is None or value == '':
        sym = symbol if symbol else '$'
        return f"{sym} 0"
    try:
        val = float(value)
        is_negative = val < 0
        val = abs(val)

        sym = symbol if symbol else '₹'
        
        # Global Western formatting for $, £, € vs Indian grouping for ₹
        if sym in ['$', 'USD', 'US$']:
            sym = '$'
            int_part = int(math.floor(val))
            dec_part = round(val - int_part, 2)
            dec_str = f".{int(round(dec_part * 100)):02d}" if dec_part > 0 else ""
            formatted = f"{int_part:,}{dec_str}"
        elif sym in ['£', 'GBP']:
            sym = '£'
            int_part = int(math.floor(val))
            dec_part = round(val - int_part, 2)
            dec_str = f".{int(round(dec_part * 100)):02d}" if dec_part > 0 else ""
            formatted = f"{int_part:,}{dec_str}"
        elif sym in ['€', 'EUR']:
            sym = '€'
            int_part = int(math.floor(val))
            dec_part = round(val - int_part, 2)
            dec_str = f".{int(round(dec_part * 100)):02d}" if dec_part > 0 else ""
            formatted = f"{int_part:,}{dec_str}"
        else:
            sym = '₹'
            int_part = int(math.floor(val))
            dec_part = round(val - int_part, 2)
            dec_str = f".{int(round(dec_part * 100)):02d}" if dec_part > 0 else ""

            s = str(int_part)
            if len(s) <= 3:
                formatted = s + dec_str
            else:
                last3 = s[-3:]
                remaining = s[:-3]
                groups = []
                while remaining:
                    groups.append(remaining[-2:])
                    remaining = remaining[:-2]
                groups.reverse()
                formatted = ",".join(groups) + "," + last3 + dec_str

        res = f"{sym} {formatted}"
        return f"-{res}" if is_negative else res
    except (ValueError, TypeError):
        sym = symbol if symbol else '$'
        return f"{sym} {value}"

@register.filter(name='status_badge')
def status_badge_class(status):
    """
    Returns appropriate Bootstrap badge color class for Udhaar / Payment / Sale statuses.
    """
    status_map = {
        'Paid': 'bg-success-subtle text-success border-success-subtle',
        'Verified': 'bg-success-subtle text-success border-success-subtle',
        'Partially Paid': 'bg-warning-subtle text-warning border-warning-subtle',
        'Payment Promised': 'bg-info-subtle text-info border-info-subtle',
        'Due': 'bg-primary-subtle text-primary border-primary-subtle',
        'Overdue': 'bg-danger-subtle text-danger border-danger-subtle',
        'Disputed': 'bg-dark-subtle text-dark border-dark-subtle',
        'Payment Claimed': 'bg-warning-subtle text-warning border-warning-subtle',
        'Pending Verification': 'bg-info-subtle text-info border-info-subtle',
    }
    return status_map.get(status, 'bg-secondary-subtle text-secondary border-secondary-subtle')
