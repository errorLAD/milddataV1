import logging

logger = logging.getLogger(__name__)


class RegionDetectionMiddleware:
    """
    Middleware to automatically detect customer's country/region using privacy-conscious HTTP headers,
    and allow seamless manual override via query parameter or session setting.
    
    Regions:
      - 'IN': India (INR / ₹) — Starting price ₹199/month (18% GST applicable)
      - 'INT': International (USD / $) — Starting price $5/month
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Check query parameter manual override e.g. ?region=IN or ?region=INT or ?currency=INR or ?currency=USD
        param_region = request.GET.get("region", "").upper()
        param_currency = request.GET.get("currency", "").upper()

        if param_region in ("IN", "INT"):
            request.session["region"] = param_region
            request.session["currency"] = "INR" if param_region == "IN" else "USD"
            request.session.modified = True
        elif param_currency in ("INR", "USD"):
            request.session["currency"] = param_currency
            request.session["region"] = "IN" if param_currency == "INR" else "INT"
            request.session.modified = True

        # 2. Check session
        region = request.session.get("region")
        
        # 3. Auto-detect from privacy-conscious request headers if session region is unset
        if not region:
            country_code = (
                request.META.get("HTTP_CF_IPCOUNTRY")
                or request.META.get("HTTP_X_COUNTRY_CODE")
                or request.META.get("HTTP_CLOUDFLARE_IPCOUNTRY")
                or ""
            ).upper()

            if country_code == "IN":
                region = "IN"
            elif country_code and country_code != "XX":
                region = "INT"
            else:
                accept_lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "").lower()
                if "en-in" in accept_lang or "hi" in accept_lang or "mai" in accept_lang:
                    region = "IN"
                else:
                    region = "IN"

            request.session["region"] = region
            request.session["currency"] = "INR" if region == "IN" else "USD"
            request.session.modified = True

        # 4. Attach attributes to request object for easy access across views & templates
        request.region = request.session.get("region", "IN")
        request.currency = request.session.get("currency", "INR" if request.region == "IN" else "USD")

        response = self.get_response(request)
        return response
