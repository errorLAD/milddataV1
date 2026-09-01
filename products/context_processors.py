def currency_context(request):
    """
    Context processor for region, currency, and billing cycle options.
    - Regions: 'IN' (India, ₹199/mo) | 'INT' (International, $5/mo)
    - Billing Cycles: 'monthly' | 'yearly' (2 months free / ~17% discount)
    """
    # Allow billing cycle toggle via GET parameter e.g. ?billing=yearly or ?billing=monthly
    billing_param = request.GET.get("billing", "").lower()
    if billing_param in ("monthly", "yearly"):
        request.session["billing_cycle"] = billing_param

    region = getattr(request, "region", request.session.get("region", "IN"))
    currency = getattr(request, "currency", request.session.get("currency", "INR" if region == "IN" else "USD"))
    billing_cycle = request.session.get("billing_cycle", "monthly")

    cycle_suffix = "/yr" if billing_cycle == "yearly" else "/mo"

    if currency == "USD" or region == "INT":
        starting_price = "$50/yr" if billing_cycle == "yearly" else "$5/mo"
        return {
            "active_region": "INT",
            "active_currency": "USD",
            "currency_symbol": "$",
            "currency_code": "USD",
            "billing_cycle": billing_cycle,
            "cycle_suffix": cycle_suffix,
            "starting_price_display": starting_price,
            "region_label": "International ($5/mo)",
            "tax_label": "Standard Sales Tax Excluded",
            "tax_rate_percent": "0",
        }
    
    starting_price = "₹1,990/yr" if billing_cycle == "yearly" else "₹199/mo"
    return {
        "active_region": "IN",
        "active_currency": "INR",
        "currency_symbol": "₹",
        "currency_code": "INR",
        "billing_cycle": billing_cycle,
        "cycle_suffix": cycle_suffix,
        "starting_price_display": starting_price,
        "region_label": "India (₹199/mo)",
        "tax_label": "GST 18%",
        "tax_rate_percent": "18",
    }
