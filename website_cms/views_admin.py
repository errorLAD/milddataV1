import csv
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from products.models import DemoLead, Order, Product
from products.saas_registry import SAAS_PRODUCTS

from .forms import (
    FAQForm,
    BlogCategoryForm,
    BlogPostForm,
    ContactLeadForm,
    FooterConfigForm,
    HomePageHeroForm,
    HomeStatForm,
    HomeWhyChooseForm,
    LegalPageForm,
    MediaAssetForm,
    NavigationItemForm,
    NewsletterSubscriberForm,
    ProductCMSForm,
    ProjectForm,
    SEOSettingForm,
    ServiceForm,
    SiteSettingsForm,
    TeamMemberForm,
    TestimonialForm,
    UserPermissionRoleForm,
)
from .models import (
    FAQ,
    AuditLog,
    BlogCategory,
    BlogPost,
    ContactLead,
    FooterConfig,
    HomePageHero,
    HomeStat,
    HomeWhyChoose,
    LegalPage,
    MediaAsset,
    NavigationItem,
    NewsletterSubscriber,
    Project,
    SEOSetting,
    Service,
    SiteSettings,
    TeamMember,
    Testimonial,
    UserPermissionRole,
)
from .utils import get_client_ip, require_cms_admin

User = get_user_model()


@login_required
@require_cms_admin("view")
def dashboard_view(request):
    """
    Executive CMS Admin Dashboard featuring high-level metrics, quick action shortcuts,
    and real-time lead/order feeds.
    """
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    saas_products_count = len(SAAS_PRODUCTS)
    services_count = Service.objects.count()
    projects_count = Project.objects.count()
    
    blog_published = BlogPost.objects.filter(status="published").count()
    blog_drafts = BlogPost.objects.filter(status="draft").count()
    total_blog_posts = BlogPost.objects.count()

    total_contact_leads = ContactLead.objects.filter(lead_type="contact").count()
    new_contact_leads = ContactLead.objects.filter(lead_type="contact", status="new").count()
    
    demo_requests_count = ContactLead.objects.filter(lead_type="demo").count() + DemoLead.objects.count()
    trial_requests_count = ContactLead.objects.filter(lead_type="trial").count()
    newsletter_subscribers_count = NewsletterSubscriber.objects.count()

    total_orders = Order.objects.count()
    paid_orders = Order.objects.filter(payment_status="paid").count()

    recent_leads = ContactLead.objects.all()[:8]
    recent_audit_logs = AuditLog.objects.all()[:6]

    return render(
        request,
        "cms_admin/dashboard.html",
        {
            "total_products": total_products,
            "active_products": active_products,
            "saas_products_count": saas_products_count,
            "services_count": services_count,
            "projects_count": projects_count,
            "blog_published": blog_published,
            "blog_drafts": blog_drafts,
            "total_blog_posts": total_blog_posts,
            "total_contact_leads": total_contact_leads,
            "new_contact_leads": new_contact_leads,
            "demo_requests_count": demo_requests_count,
            "trial_requests_count": trial_requests_count,
            "newsletter_subscribers_count": newsletter_subscribers_count,
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "recent_leads": recent_leads,
            "recent_audit_logs": recent_audit_logs,
        },
    )


@login_required
@require_cms_admin("view")
def homepage_admin_view(request):
    """
    Homepage CMS Controller: Hero, Stats, Why Choose Milda Data, Services, Testimonials, FAQs, CTA.
    """
    hero = HomePageHero.objects.first() or HomePageHero.objects.create()
    stats = HomeStat.objects.all()
    why_items = HomeWhyChoose.objects.all()
    services = Service.objects.all()
    testimonials = Testimonial.objects.all()
    faqs = FAQ.objects.filter(placement__in=["global", "homepage"])
    products = Product.objects.filter(is_active=True)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_hero":
            hero_form = HomePageHeroForm(request.POST, request.FILES, instance=hero)
            if hero_form.is_valid():
                hero_form.save()
                AuditLog.log(request.user, "Updated Homepage Hero", "HomePageHero", hero.pk, ip_address=get_client_ip(request))
                messages.success(request, "Homepage Hero updated successfully.")
                return redirect("website_cms:homepage_admin")
        elif action == "add_stat":
            stat_form = HomeStatForm(request.POST)
            if stat_form.is_valid():
                stat_form.save()
                messages.success(request, "New Stat added successfully.")
                return redirect("website_cms:homepage_admin")
        elif action == "add_why":
            why_form = HomeWhyChooseForm(request.POST, request.FILES)
            if why_form.is_valid():
                why_form.save()
                messages.success(request, "Why Milda Data feature added.")
                return redirect("website_cms:homepage_admin")

    hero_form = HomePageHeroForm(instance=hero)
    stat_form = HomeStatForm()
    why_form = HomeWhyChooseForm()

    return render(
        request,
        "cms_admin/homepage.html",
        {
            "hero_form": hero_form,
            "stat_form": stat_form,
            "why_form": why_form,
            "hero": hero,
            "stats": stats,
            "why_items": why_items,
            "services": services,
            "testimonials": testimonials,
            "faqs": faqs,
            "products": products,
        },
    )


@login_required
@require_cms_admin("view")
def products_admin_list(request):
    products = Product.objects.all()
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    return render(request, "cms_admin/products_list.html", {"products": products, "saas_registry": SAAS_PRODUCTS, "query": query})


@login_required
@require_cms_admin("publish")
def product_admin_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductCMSForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            AuditLog.log(request.user, f"Edited Product '{product.name}'", "Product", product.pk, ip_address=get_client_ip(request))
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect("website_cms:products_list")
    else:
        form = ProductCMSForm(instance=product)
    return render(request, "cms_admin/product_form.html", {"form": form, "product": product})


@login_required
@require_cms_admin("publish")
def product_admin_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product_name = product.name
        product.delete()
        AuditLog.log(request.user, f"Deleted product '{product_name}'", "Product", pk, ip_address=get_client_ip(request))
        messages.success(request, f"Product '{product_name}' deleted successfully.")
        return redirect("website_cms:products_list")

    return render(request, "cms_admin/confirm_delete.html", {
        "object": product,
        "object_type": "Product",
        "cancel_url": "website_cms:products_list",
    })


@login_required
@require_cms_admin("view")
def services_admin_list(request):
    services = Service.objects.all()
    return render(request, "cms_admin/services_list.html", {"services": services})


@login_required
@require_cms_admin("publish")
def service_admin_create_edit(request, pk=None):
    service = get_object_or_404(Service, pk=pk) if pk else None
    if request.method == "POST":
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            obj = form.save()
            action = f"Updated Service '{obj.name}'" if pk else f"Created Service '{obj.name}'"
            AuditLog.log(request.user, action, "Service", obj.pk, ip_address=get_client_ip(request))
            messages.success(request, f"Service '{obj.name}' saved successfully.")
            return redirect("website_cms:services_list")
    else:
        form = ServiceForm(instance=service)
    return render(request, "cms_admin/service_form.html", {"form": form, "service": service})


@login_required
@require_cms_admin("delete")
def service_admin_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    name = service.name
    service.delete()
    AuditLog.log(request.user, f"Deleted Service '{name}'", "Service", pk, ip_address=get_client_ip(request))
    messages.success(request, f"Service '{name}' deleted.")
    return redirect("website_cms:services_list")


@login_required
@require_cms_admin("view")
def projects_admin_list(request):
    projects = Project.objects.all()
    return render(request, "cms_admin/projects_list.html", {"projects": projects})


@login_required
@require_cms_admin("publish")
def project_admin_create_edit(request, pk=None):
    project = get_object_or_404(Project, pk=pk) if pk else None
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            obj = form.save()
            action = f"Updated Project '{obj.title}'" if pk else f"Created Project '{obj.title}'"
            AuditLog.log(request.user, action, "Project", obj.pk, ip_address=get_client_ip(request))
            messages.success(request, f"Project '{obj.title}' saved successfully.")
            return redirect("website_cms:projects_list")
    else:
        form = ProjectForm(instance=project)
    return render(request, "cms_admin/project_form.html", {"form": form, "project": project})


@login_required
@require_cms_admin("delete")
def project_admin_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    title = project.title
    project.delete()
    AuditLog.log(request.user, f"Deleted Project '{title}'", "Project", pk, ip_address=get_client_ip(request))
    messages.success(request, f"Project '{title}' deleted.")
    return redirect("website_cms:projects_list")


@login_required
@require_cms_admin("view")
def blog_admin_list(request):
    status_filter = request.GET.get("status", "")
    posts = BlogPost.objects.all()
    if status_filter:
        posts = posts.filter(status=status_filter)
    categories = BlogCategory.objects.all()
    return render(request, "cms_admin/blog_list.html", {"posts": posts, "categories": categories, "active_status": status_filter})


@login_required
@require_cms_admin("publish")
def blog_admin_create_edit(request, pk=None):
    post = get_object_or_404(BlogPost, pk=pk) if pk else None
    if request.method == "POST":
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            obj = form.save()
            action = f"Updated Blog Post '{obj.title}' ({obj.status})" if pk else f"Created Blog Post '{obj.title}' ({obj.status})"
            AuditLog.log(request.user, action, "BlogPost", obj.pk, ip_address=get_client_ip(request))
            messages.success(request, f"Blog Post '{obj.title}' saved as {obj.get_status_display()}.")
            return redirect("website_cms:blog_list")
    else:
        form = BlogPostForm(instance=post)
    return render(request, "cms_admin/blog_form.html", {"form": form, "post": post})


@login_required
@require_cms_admin("delete")
def blog_admin_delete(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    title = post.title
    post.delete()
    AuditLog.log(request.user, f"Deleted Blog Post '{title}'", "BlogPost", pk, ip_address=get_client_ip(request))
    messages.success(request, f"Article '{title}' deleted.")
    return redirect("website_cms:blog_list")


@login_required
@require_cms_admin("view")
def team_admin_list(request):
    team = TeamMember.objects.all()
    return render(request, "cms_admin/team_list.html", {"team": team})


@login_required
@require_cms_admin("publish")
def team_admin_create_edit(request, pk=None):
    member = get_object_or_404(TeamMember, pk=pk) if pk else None
    if request.method == "POST":
        form = TeamMemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Team member '{obj.name}' saved.")
            return redirect("website_cms:team_list")
    else:
        form = TeamMemberForm(instance=member)
    return render(request, "cms_admin/team_form.html", {"form": form, "member": member})


@login_required
@require_cms_admin("view")
def testimonials_admin_list(request):
    testimonials = Testimonial.objects.all()
    return render(request, "cms_admin/testimonials_list.html", {"testimonials": testimonials})


@login_required
@require_cms_admin("publish")
def testimonial_admin_create_edit(request, pk=None):
    testimonial = get_object_or_404(Testimonial, pk=pk) if pk else None
    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES, instance=testimonial)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Testimonial from '{obj.customer_name}' saved.")
            return redirect("website_cms:testimonials_list")
    else:
        form = TestimonialForm(instance=testimonial)
    return render(request, "cms_admin/testimonial_form.html", {"form": form, "testimonial": testimonial})


@login_required
@require_cms_admin("view")
def faqs_admin_list(request):
    faqs = FAQ.objects.all()
    return render(request, "cms_admin/faqs_list.html", {"faqs": faqs})


@login_required
@require_cms_admin("publish")
def faq_admin_create_edit(request, pk=None):
    faq = get_object_or_404(FAQ, pk=pk) if pk else None
    if request.method == "POST":
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "FAQ entry saved.")
            return redirect("website_cms:faqs_list")
    else:
        form = FAQForm(instance=faq)
    return render(request, "cms_admin/faq_form.html", {"form": form, "faq": faq})


@login_required
@require_cms_admin("view")
def leads_admin_list(request):
    lead_type = request.GET.get("type", "")
    status = request.GET.get("status", "")
    leads = ContactLead.objects.all()

    if lead_type:
        leads = leads.filter(lead_type=lead_type)
    if status:
        leads = leads.filter(status=status)

    demo_leads_legacy = DemoLead.objects.all()
    subscribers = NewsletterSubscriber.objects.all()

    return render(
        request,
        "cms_admin/leads_list.html",
        {
            "leads": leads,
            "demo_leads_legacy": demo_leads_legacy,
            "subscribers": subscribers,
            "active_type": lead_type,
            "active_status": status,
        },
    )


@login_required
@require_cms_admin("publish")
def lead_admin_detail_update(request, pk):
    lead = get_object_or_404(ContactLead, pk=pk)
    if request.method == "POST":
        form = ContactLeadForm(request.POST, instance=lead)
        if form.is_valid():
            obj = form.save()
            AuditLog.log(request.user, f"Updated Lead status to '{obj.status}'", "ContactLead", obj.pk, ip_address=get_client_ip(request))
            messages.success(request, f"Lead record for '{obj.name}' updated.")
            return redirect("website_cms:leads_list")
    else:
        form = ContactLeadForm(instance=lead)
    return render(request, "cms_admin/lead_detail.html", {"form": form, "lead": lead})


@login_required
@require_cms_admin("view")
def export_newsletter_subscribers(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="milda_newsletter_subscribers.csv"'

    writer = csv.writer(response)
    writer.writerow(["ID", "Email", "Status", "Source", "Date Subscribed"])

    for sub in NewsletterSubscriber.objects.all():
        writer.writerow([sub.id, sub.email, "Active" if sub.is_active else "Unsubscribed", sub.source, sub.created_at.strftime("%Y-%m-%d %H:%M")])

    return response


@login_required
@require_cms_admin("view")
def media_library_view(request):
    media_assets = MediaAsset.objects.all()
    query = request.GET.get("q", "").strip()
    media_type = request.GET.get("type", "")

    if query:
        media_assets = media_assets.filter(Q(title__icontains=query) | Q(alt_text__icontains=query))
    if media_type:
        media_assets = media_assets.filter(media_type=media_type)

    if request.method == "POST":
        form = MediaAssetForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save()
            AuditLog.log(request.user, f"Uploaded Media '{asset.title}'", "MediaAsset", asset.pk, ip_address=get_client_ip(request))
            messages.success(request, f"Media file '{asset.title}' uploaded successfully.")
            return redirect("website_cms:media_library")
    else:
        form = MediaAssetForm()

    return render(request, "cms_admin/media_library.html", {"form": form, "media_assets": media_assets, "query": query, "active_type": media_type})


@login_required
@require_cms_admin("delete")
def media_asset_delete(request, pk):
    asset = get_object_or_404(MediaAsset, pk=pk)
    title = asset.title
    asset.delete()
    AuditLog.log(request.user, f"Deleted Media Asset '{title}'", "MediaAsset", pk, ip_address=get_client_ip(request))
    messages.success(request, f"Media asset '{title}' removed.")
    return redirect("website_cms:media_library")


@login_required
@require_cms_admin("view")
def navigation_footer_admin(request):
    nav_items = NavigationItem.objects.filter(parent__isnull=True).prefetch_related("children")
    footer = FooterConfig.get_config()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_footer":
            footer_form = FooterConfigForm(request.POST, instance=footer)
            if footer_form.is_valid():
                footer_form.save()
                messages.success(request, "Footer configuration updated.")
                return redirect("website_cms:navigation_footer_admin")
        elif action == "add_nav":
            nav_form = NavigationItemForm(request.POST)
            if nav_form.is_valid():
                nav_form.save()
                messages.success(request, "Navigation item added.")
                return redirect("website_cms:navigation_footer_admin")

    footer_form = FooterConfigForm(instance=footer)
    nav_form = NavigationItemForm()

    return render(request, "cms_admin/navigation_footer.html", {"nav_items": nav_items, "footer": footer, "footer_form": footer_form, "nav_form": nav_form})


@login_required
@require_cms_admin("settings")
def seo_settings_admin(request):
    seo_settings = SEOSetting.objects.all()

    if request.method == "POST":
        setting_id = request.POST.get("setting_id")
        instance = get_object_or_404(SEOSetting, pk=setting_id) if setting_id else None
        form = SEOSettingForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"SEO settings for '{obj.get_page_identifier_display()}' updated.")
            return redirect("website_cms:seo_settings_admin")
    else:
        form = SEOSettingForm()

    return render(request, "cms_admin/seo_settings.html", {"seo_settings": seo_settings, "form": form})


@login_required
@require_cms_admin("settings")
def site_settings_admin(request):
    settings_obj = SiteSettings.get_settings()
    if request.method == "POST":
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            AuditLog.log(request.user, "Updated Global Site Settings", "SiteSettings", settings_obj.pk, ip_address=get_client_ip(request))
            messages.success(request, "Global site settings saved.")
            return redirect("website_cms:site_settings_admin")
    else:
        form = SiteSettingsForm(instance=settings_obj)
    return render(request, "cms_admin/site_settings.html", {"form": form, "settings_obj": settings_obj})


@login_required
@require_cms_admin("view")
def audit_logs_view(request):
    logs = AuditLog.objects.all()[:100]
    return render(request, "cms_admin/audit_logs.html", {"logs": logs})


@login_required
@require_cms_admin("view")
def universal_search_view(request):
    query = request.GET.get("q", "").strip()
    results = {
        "products": Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query)) if query else [],
        "services": Service.objects.filter(Q(name__icontains=query) | Q(short_description__icontains=query)) if query else [],
        "projects": Project.objects.filter(Q(title__icontains=query) | Q(short_description__icontains=query)) if query else [],
        "blog_posts": BlogPost.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)) if query else [],
        "faqs": FAQ.objects.filter(Q(question__icontains=query) | Q(answer__icontains=query)) if query else [],
        "leads": ContactLead.objects.filter(Q(name__icontains=query) | Q(email__icontains=query) | Q(company__icontains=query)) if query else [],
    }
    return render(request, "cms_admin/search_results.html", {"query": query, "results": results})


@login_required
@require_cms_admin("settings")
def user_permissions_admin(request):
    roles = UserPermissionRole.objects.all()
    users = User.objects.all()

    if request.method == "POST":
        form = UserPermissionRoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User permission role updated.")
            return redirect("website_cms:user_permissions_admin")
    else:
        form = UserPermissionRoleForm()

    return render(request, "cms_admin/user_permissions.html", {"roles": roles, "users": users, "form": form})


@login_required
def draft_preview_view(request, content_type, slug_or_id):
    """
    Secure authenticated draft preview for unpublished blog posts, services, or projects.
    """
    if not check_cms_permission(request.user):
        return HttpResponse("Unauthorized draft preview", status=403)

    if content_type == "blog":
        post = get_object_or_404(BlogPost, slug=slug_or_id)
        return render(request, "website/blog_detail.html", {"post": post, "is_preview": True})
    elif content_type == "service":
        service = get_object_or_404(Service, slug=slug_or_id)
        return render(request, "website/service_detail.html", {"service": service, "is_preview": True})
    elif content_type == "project":
        project = get_object_or_404(Project, slug=slug_or_id)
        return render(request, "website/project_detail.html", {"project": project, "is_preview": True})

    return HttpResponse("Unknown content type", status=404)


def admin_login_view(request):
    """
    Dedicated Login View specifically for the Milda Data CMS Admin Panel.
    Auto-provisions the primary admin superuser if absent in production.
    """
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect("website_cms:dashboard")

    next_url = request.GET.get("next") or request.POST.get("next") or "/admin/dashboard/"

    if request.method == "POST":
        username_input = request.POST.get("username", "").strip()
        password_input = request.POST.get("password", "").strip()

        if not username_input or not password_input:
            messages.error(request, "Please enter both admin username/email and password.")
            return render(request, "cms_admin/admin_login.html", {"next": next_url, "username_val": username_input})

        # Auto-provision/synchronize primary admin superuser if needed
        if username_input.lower() in ("admin", "ab.mishra@yahoo.com") and password_input == "Admin@1234":
            try:
                user_obj = User.objects.filter(Q(username__iexact="admin") | Q(email__iexact="ab.mishra@yahoo.com")).first()
                if not user_obj:
                    user_obj = User.objects.create_superuser(
                        username="admin",
                        email="ab.mishra@yahoo.com",
                        password="Admin@1234",
                    )
                user_obj.email = "ab.mishra@yahoo.com"
                user_obj.is_staff = True
                user_obj.is_superuser = True
                user_obj.set_password("Admin@1234")
                user_obj.save()
            except Exception:
                pass

        # Try username or email authentication
        user = authenticate(request, username=username_input, password=password_input)
        if not user:
            # Check if email was passed instead of username
            try:
                user_obj = User.objects.get(email__iexact=username_input)
                user = authenticate(request, username=user_obj.username, password=password_input)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

        if user and user.is_active:
            if user.is_staff or user.is_superuser or hasattr(user, "cms_role"):
                login(request, user)
                AuditLog.log(user, "Admin Logged In via Dedicated Admin Panel", "User", user.pk, ip_address=get_client_ip(request))
                messages.success(request, f"Welcome back, {user.email or user.username}!")
                return redirect(next_url)
            else:
                messages.error(request, "Access Denied: Your account does not have administrative permissions.")
        else:
            messages.error(request, "Invalid administrator username or password.")

    return render(request, "cms_admin/admin_login.html", {"next": next_url})


def admin_logout_view(request):
    """
    Dedicated Logout View for the CMS Admin Panel.
    """
    if request.user.is_authenticated:
        AuditLog.log(request.user, "Admin Logged Out", "User", request.user.pk, ip_address=get_client_ip(request))
        logout(request)
    messages.info(request, "You have been logged out of the CMS Admin Panel.")
    return redirect("website_cms:admin_login")

