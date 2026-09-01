from django.shortcuts import render
from products.saas_registry import get_all_saas_products
from website_cms.models import (
    FAQ,
    HomePageHero,
    HomeStat,
    HomeWhyChoose,
    Project,
    Service,
    Testimonial,
)


def home(request):
    currency = getattr(request, "currency", request.session.get("currency", "INR"))
    billing_cycle = request.session.get("billing_cycle", "monthly")
    saas_products = get_all_saas_products(currency=currency, billing_cycle=billing_cycle)

    hero = HomePageHero.objects.first()
    stats = HomeStat.objects.filter(is_active=True)
    why_items = HomeWhyChoose.objects.filter(is_active=True)
    cms_services = Service.objects.filter(status="active")[:6]
    cms_projects = Project.objects.filter(status="published")[:3]
    cms_testimonials = Testimonial.objects.filter(is_approved=True, is_featured=True)
    cms_faqs = FAQ.objects.filter(placement__in=["global", "homepage"], is_active=True)

    return render(
        request,
        "home.html",
        {
            "saas_products": saas_products,
            "cms_hero": hero,
            "cms_stats": stats,
            "cms_why_items": why_items,
            "cms_services": cms_services,
            "cms_projects": cms_projects,
            "cms_testimonials": cms_testimonials,
            "cms_faqs": cms_faqs,
        },
    )
