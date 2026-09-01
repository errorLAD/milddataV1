def currency_context(request):
    """
    Global Context Processor:
    Provides `currency_symbol`, `currency_code`, and `country_name` across all templates.
    """
    currency_symbol = '$'
    currency_code = 'USD'
    country_name = 'United States'
    country_code = 'US'

    if hasattr(request, 'user') and request.user.is_authenticated:
        if hasattr(request.user, 'organization') and request.user.organization:
            org = request.user.organization
            currency_symbol = org.currency_symbol or '$'
            currency_code = org.currency_code or 'USD'
            country_name = org.country_name or 'United States'
            country_code = org.country_code or 'US'

    return {
        'currency_symbol': currency_symbol,
        'currency_code': currency_code,
        'country_name': country_name,
        'country_code': country_code,
    }
