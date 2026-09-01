import math

COUNTRY_PROFILES = {
    'IN': {
        'code': 'IN',
        'name': 'India',
        'flag': '🇮🇳',
        'currency': 'INR',
        'symbol': '₹',
        'date_format': 'DD/MM/YYYY',
        'django_date_format': 'd/m/Y',
        'timezone': 'Asia/Kolkata',
        'phone_code': '+91',
        'tax_label': 'GST',
        'number_format': 'indian',
        'example_price': '₹ 1,499'
    },
    'US': {
        'code': 'US',
        'name': 'United States',
        'flag': '🇺🇸',
        'currency': 'USD',
        'symbol': '$',
        'date_format': 'MM/DD/YYYY',
        'django_date_format': 'm/d/Y',
        'timezone': 'America/New_York',
        'phone_code': '+1',
        'tax_label': 'Sales Tax',
        'number_format': 'standard',
        'example_price': '$ 19.99'
    },
    'GB': {
        'code': 'GB',
        'name': 'United Kingdom',
        'flag': '🇬🇧',
        'currency': 'GBP',
        'symbol': '£',
        'date_format': 'DD/MM/YYYY',
        'django_date_format': 'd/m/Y',
        'timezone': 'Europe/London',
        'phone_code': '+44',
        'tax_label': 'VAT',
        'number_format': 'standard',
        'example_price': '£ 19.99'
    },
    'EU': {
        'code': 'EU',
        'name': 'European Union',
        'flag': '🇪🇺',
        'currency': 'EUR',
        'symbol': '€',
        'date_format': 'DD/MM/YYYY',
        'django_date_format': 'd/m/Y',
        'timezone': 'Europe/Paris',
        'phone_code': '+33',
        'tax_label': 'VAT',
        'number_format': 'standard',
        'example_price': '€ 19.99'
    },
    'CA': {
        'code': 'CA',
        'name': 'Canada',
        'flag': '🇨🇦',
        'currency': 'CAD',
        'symbol': '$',
        'date_format': 'YYYY-MM-DD',
        'django_date_format': 'Y-m-d',
        'timezone': 'America/Toronto',
        'phone_code': '+1',
        'tax_label': 'GST/HST',
        'number_format': 'standard',
        'example_price': '$ 19.99'
    },
    'AU': {
        'code': 'AU',
        'name': 'Australia',
        'flag': '🇦🇺',
        'currency': 'AUD',
        'symbol': '$',
        'date_format': 'DD/MM/YYYY',
        'django_date_format': 'd/m/Y',
        'timezone': 'Australia/Sydney',
        'phone_code': '+61',
        'tax_label': 'GST',
        'number_format': 'standard',
        'example_price': '$ 19.99'
    },
    'AE': {
        'code': 'AE',
        'name': 'United Arab Emirates',
        'flag': '🇦🇪',
        'currency': 'AED',
        'symbol': 'AED',
        'date_format': 'DD/MM/YYYY',
        'django_date_format': 'd/m/Y',
        'timezone': 'Asia/Dubai',
        'phone_code': '+971',
        'tax_label': 'VAT',
        'number_format': 'standard',
        'example_price': 'AED 19.99'
    },
    'SG': {
        'code': 'SG',
        'name': 'Singapore',
        'flag': '🇸🇬',
        'currency': 'SGD',
        'symbol': '$',
        'date_format': 'DD/MM/YYYY',
        'django_date_format': 'd/m/Y',
        'timezone': 'Asia/Singapore',
        'phone_code': '+65',
        'tax_label': 'GST',
        'number_format': 'standard',
        'example_price': '$ 19.99'
    },
    'JP': {
        'code': 'JP',
        'name': 'Japan',
        'flag': '🇯🇵',
        'currency': 'JPY',
        'symbol': '¥',
        'date_format': 'YYYY/MM/DD',
        'django_date_format': 'Y/m/d',
        'timezone': 'Asia/Tokyo',
        'phone_code': '+81',
        'tax_label': 'Consumption Tax',
        'number_format': 'standard',
        'example_price': '¥ 1,999'
    },
    'DE': {
        'code': 'DE',
        'name': 'Germany',
        'flag': '🇩🇪',
        'currency': 'EUR',
        'symbol': '€',
        'date_format': 'DD.MM.YYYY',
        'django_date_format': 'd.m.Y',
        'timezone': 'Europe/Berlin',
        'phone_code': '+49',
        'tax_label': 'MwSt',
        'number_format': 'standard',
        'example_price': '€ 19.99'
    },
    'SA': {
        'code': 'SA',
        'name': 'Saudi Arabia',
        'flag': '🇸🇦',
        'currency': 'SAR',
        'symbol': 'SR',
        'date_format': 'DD/MM/YYYY',
        'django_date_format': 'd/m/Y',
        'timezone': 'Asia/Riyadh',
        'phone_code': '+966',
        'tax_label': 'VAT',
        'number_format': 'standard',
        'example_price': 'SR 19.99'
    }
}

DEFAULT_COUNTRY_CODE = 'US'


def get_country_profile(country_code):
    code = (country_code or '').upper().strip()
    return COUNTRY_PROFILES.get(code, COUNTRY_PROFILES[DEFAULT_COUNTRY_CODE])


def get_country_choices():
    return [(k, f"{v['flag']} {v['name']} ({v['currency']})") for k, v in COUNTRY_PROFILES.items()]


def format_money(value, symbol='$', number_format='standard'):
    if value is None or value == '':
        sym = symbol if symbol else '$'
        return f"{sym} 0"
    try:
        val = float(value)
        is_negative = val < 0
        val = abs(val)

        sym = symbol if symbol else '$'

        if number_format == 'indian' or sym == '₹':
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
        else:
            int_part = int(math.floor(val))
            dec_part = round(val - int_part, 2)
            dec_str = f".{int(round(dec_part * 100)):02d}" if dec_part > 0 else ""
            formatted = f"{int_part:,}{dec_str}"

        res = f"{sym} {formatted}"
        return f"-{res}" if is_negative else res
    except (ValueError, TypeError):
        sym = symbol if symbol else '$'
        return f"{sym} {value}"
