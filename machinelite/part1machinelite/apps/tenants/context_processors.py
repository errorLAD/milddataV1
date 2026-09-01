def tenant_context(request):
    """
    Makes tenant, organization name, currency symbol, user role, and Guest Mode status accessible in all templates.
    """
    tenant = getattr(request, 'tenant', None)
    is_guest = getattr(request, 'is_guest', False)
    profile = None
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        
    return {
        'current_tenant': tenant,
        'org_name': tenant.name if tenant else ("Demo Fleet (Guest Mode)" if is_guest else "Machine OS Enterprise"),
        'currency_symbol': tenant.currency_symbol if tenant else "₹",
        'user_profile': profile,
        'user_role': profile.role if profile else ('guest' if is_guest else 'admin'),
        'is_guest': is_guest,
    }
