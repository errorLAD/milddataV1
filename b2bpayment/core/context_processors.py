from core.localization import get_country_profile

def tenant_context(request):
    """
    Context processor that adds the current business context.
    """
    if hasattr(request, 'business') and request.business:
        return {'current_business': request.business}
    return {}

def localization_context(request):
    """
    Context processor providing account-level regional settings to all templates.
    """
    if hasattr(request, 'business') and request.business:
        try:
            from settings_app.models import BusinessSettings
            b_settings, _ = BusinessSettings.objects.get_or_create(business=request.business)
            return {
                'business_country': b_settings.country,
                'business_currency': b_settings.currency,
                'business_currency_symbol': b_settings.currency_symbol,
                'business_tax_label': b_settings.tax_label,
                'business_date_format': b_settings.date_format,
                'business_phone_code': b_settings.phone_code,
                'business_timezone': b_settings.timezone,
                'business_number_format': b_settings.number_format,
                'business_settings': b_settings,
            }
        except Exception:
            pass

    # Default fallback for guest or unauthenticated views
    profile = get_country_profile('US')
    return {
        'business_country': profile['code'],
        'business_currency': profile['currency'],
        'business_currency_symbol': profile['symbol'],
        'business_tax_label': profile['tax_label'],
        'business_date_format': profile['date_format'],
        'business_phone_code': profile['phone_code'],
        'business_timezone': profile['timezone'],
        'business_number_format': profile['number_format'],
        'business_settings': None,
    }
