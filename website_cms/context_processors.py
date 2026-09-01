from .models import FooterConfig, NavigationItem, SEOSetting, SiteSettings


def cms_global_context(request):
    """
    Inject global site settings, navigation menus, footer details, and default SEO metadata
    into all templates across the entire website.
    """
    site_settings = SiteSettings.get_settings()
    footer_config = FooterConfig.get_config()

    # Get top-level header navigation items
    header_nav = NavigationItem.objects.filter(is_active=True, parent__isnull=True).prefetch_related("children")

    # If no navigation items exist yet, provide default fallback structure
    if not header_nav.exists():
        fallback_nav = [
            {"label": "Data Labeling", "url": "/labeling/", "open_in_new_tab": False},
            {"label": "SAAS STORE", "url": "/products/", "open_in_new_tab": False, "is_special": True},
            {"label": "Services", "url": "/services/", "open_in_new_tab": False},
            {"label": "Portfolio", "url": "/projects/", "open_in_new_tab": False},
            {"label": "Blog", "url": "/blog/", "open_in_new_tab": False},
            {"label": "Contact", "url": "/contact/", "open_in_new_tab": False},
        ]
    else:
        fallback_nav = None

    # Fetch default homepage SEO settings if present
    seo_default = SEOSetting.objects.filter(page_identifier="homepage").first()

    return {
        "cms_settings": site_settings,
        "cms_footer": footer_config,
        "cms_nav_items": header_nav if header_nav.exists() else None,
        "cms_nav_fallback": fallback_nav,
        "cms_seo_default": seo_default,
    }
