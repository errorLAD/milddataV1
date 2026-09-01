from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from products.models import Product

from .models import (
    FAQ,
    BlogCategory,
    BlogPost,
    ContactLead,
    HomePageHero,
    HomeStat,
    HomeWhyChoose,
    LegalPage,
    NewsletterSubscriber,
    Project,
    SEOSetting,
    Service,
    SiteSettings,
    TeamMember,
    Testimonial,
)


def services_index(request):
    services = Service.objects.filter(status="active")
    seo = SEOSetting.objects.filter(page_identifier="services").first()
    faqs = FAQ.objects.filter(placement__in=["global", "service"], is_active=True)
    return render(request, "website/services_index.html", {"services": services, "seo": seo, "faqs": faqs})


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, status="active")
    faqs = FAQ.objects.filter(service_name__icontains=service.name, is_active=True)
    if not faqs.exists():
        faqs = FAQ.objects.filter(placement__in=["global", "service"], is_active=True)
    return render(request, "website/service_detail.html", {"service": service, "faqs": faqs})


def projects_index(request):
    category = request.GET.get("category", "")
    projects = Project.objects.filter(status="published")
    if category:
        projects = projects.filter(category__icontains=category)
    seo = SEOSetting.objects.filter(page_identifier="projects").first()
    return render(request, "website/projects_index.html", {"projects": projects, "seo": seo, "active_category": category})


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug, status="published")
    related_projects = Project.objects.filter(status="published").exclude(id=project.id)[:3]
    return render(request, "website/project_detail.html", {"project": project, "related_projects": related_projects})


def blog_index(request):
    category_slug = request.GET.get("category", "")
    query = request.GET.get("q", "").strip()

    posts = BlogPost.objects.filter(status="published")
    categories = BlogCategory.objects.all()

    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    if query:
        posts = posts.filter(title__icontains=query) | posts.filter(content__icontains=query)

    featured_post = posts.first()
    regular_posts = posts[1:] if featured_post else []

    seo = SEOSetting.objects.filter(page_identifier="blog").first()
    return render(
        request,
        "website/blog_index.html",
        {
            "featured_post": featured_post,
            "posts": regular_posts,
            "categories": categories,
            "seo": seo,
            "active_category": category_slug,
            "search_query": query,
        },
    )


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, status="published")
    post.views_count += 1
    post.save(update_fields=["views_count"])

    recent_posts = BlogPost.objects.filter(status="published").exclude(id=post.id)[:3]
    return render(request, "website/blog_detail.html", {"post": post, "recent_posts": recent_posts})


def about_us(request):
    team_members = TeamMember.objects.filter(is_active=True)
    stats = HomeStat.objects.filter(is_active=True)
    why_items = HomeWhyChoose.objects.filter(is_active=True)
    seo = SEOSetting.objects.filter(page_identifier="about").first()
    return render(request, "website/about.html", {"team_members": team_members, "stats": stats, "why_items": why_items, "seo": seo})


def contact_us(request):
    seo = SEOSetting.objects.filter(page_identifier="contact").first()
    faqs = FAQ.objects.filter(placement__in=["global", "contact"], is_active=True)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        company = request.POST.get("company", "").strip()
        message = request.POST.get("message", "").strip()
        product_or_service = request.POST.get("product_or_service", "").strip()
        lead_type = request.POST.get("lead_type", "contact")

        if not name or not email or not message:
            messages.error(request, "Please complete all required fields (Name, Email, and Message).")
            return redirect("website_cms:contact")

        lead = ContactLead.objects.create(
            lead_type=lead_type,
            name=name,
            email=email,
            phone=phone,
            company=company,
            message=message,
            product_or_service=product_or_service,
            source_page=request.path,
        )

        # Notify sales team email
        recipients = ["ab.mishra@yahoo.com"]
        subject = f"[Website {lead.get_lead_type_display()}] {name} ({company or email})"
        message_body = (
            f"New Website Contact Submission!\n\n"
            f"Type: {lead.get_lead_type_display()}\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Phone: {phone}\n"
            f"Company: {company}\n"
            f"Interested Product/Service: {product_or_service}\n\n"
            f"Message:\n{message}\n"
        )
        try:
            send_mail(subject, message_body, settings.DEFAULT_FROM_EMAIL or "noreply@mildadata.com", recipients, fail_silently=True)
        except Exception:
            pass

        messages.success(request, f"Thank you {name}! Your message has been received. Our sales & support team will contact you shortly.")
        return redirect("website_cms:contact")

    return render(request, "website/contact.html", {"seo": seo, "faqs": faqs})


def legal_page_detail(request, slug):
    page = get_object_or_404(LegalPage, slug=slug, is_published=True)
    return render(request, "website/legal_detail.html", {"page": page})


def newsletter_subscribe(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email or "@" not in email:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": "Please provide a valid email address."})
            messages.error(request, "Please enter a valid email address.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        sub, created = NewsletterSubscriber.objects.get_or_create(email=email, defaults={"is_active": True})
        if not created and not sub.is_active:
            sub.is_active = True
            sub.save(update_fields=["is_active"])

        msg = "Thank you for subscribing to Milda Data updates!"
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": msg})
        messages.success(request, msg)
    return redirect(request.META.get("HTTP_REFERER", "/"))


def newsletter_unsubscribe(request, token):
    sub = get_object_or_404(NewsletterSubscriber, unsubscribe_token=token)
    sub.is_active = False
    sub.save(update_fields=["is_active"])
    return render(request, "website/unsubscribed.html", {"email": sub.email})
