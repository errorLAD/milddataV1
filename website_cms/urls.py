from django.urls import path
from . import views_admin, views_public

app_name = "website_cms"

urlpatterns = [
    # Custom Dedicated Admin Login & Logout Routes
    path("admin/login/", views_admin.admin_login_view, name="admin_login"),
    path("admin/logout/", views_admin.admin_logout_view, name="admin_logout"),

    # Custom Admin CMS Routes
    path("admin/dashboard/", views_admin.dashboard_view, name="dashboard"),
    path("admin/cms/homepage/", views_admin.homepage_admin_view, name="homepage_admin"),
    path("admin/cms/products/", views_admin.products_admin_list, name="products_list"),
    path("admin/cms/products/<int:pk>/edit/", views_admin.product_admin_edit, name="product_edit"),
    path("admin/cms/products/<int:pk>/delete/", views_admin.product_admin_delete, name="product_delete"),
    path("admin/cms/services/", views_admin.services_admin_list, name="services_list"),
    path("admin/cms/services/create/", views_admin.service_admin_create_edit, name="service_create"),
    path("admin/cms/services/<int:pk>/edit/", views_admin.service_admin_create_edit, name="service_edit"),
    path("admin/cms/services/<int:pk>/delete/", views_admin.service_admin_delete, name="service_delete"),
    path("admin/cms/projects/", views_admin.projects_admin_list, name="projects_list"),
    path("admin/cms/projects/create/", views_admin.project_admin_create_edit, name="project_create"),
    path("admin/cms/projects/<int:pk>/edit/", views_admin.project_admin_create_edit, name="project_edit"),
    path("admin/cms/projects/<int:pk>/delete/", views_admin.project_admin_delete, name="project_delete"),
    path("admin/cms/blog/", views_admin.blog_admin_list, name="blog_list"),
    path("admin/cms/blog/create/", views_admin.blog_admin_create_edit, name="blog_create"),
    path("admin/cms/blog/<int:pk>/edit/", views_admin.blog_admin_create_edit, name="blog_edit"),
    path("admin/cms/blog/<int:pk>/delete/", views_admin.blog_admin_delete, name="blog_delete"),
    path("admin/cms/team/", views_admin.team_admin_list, name="team_list"),
    path("admin/cms/team/create/", views_admin.team_admin_create_edit, name="team_create"),
    path("admin/cms/team/<int:pk>/edit/", views_admin.team_admin_create_edit, name="team_edit"),
    path("admin/cms/testimonials/", views_admin.testimonials_admin_list, name="testimonials_list"),
    path("admin/cms/testimonials/create/", views_admin.testimonial_admin_create_edit, name="testimonial_create"),
    path("admin/cms/testimonials/<int:pk>/edit/", views_admin.testimonial_admin_create_edit, name="testimonial_edit"),
    path("admin/cms/faqs/", views_admin.faqs_admin_list, name="faqs_list"),
    path("admin/cms/faqs/create/", views_admin.faq_admin_create_edit, name="faq_create"),
    path("admin/cms/faqs/<int:pk>/edit/", views_admin.faq_admin_create_edit, name="faq_edit"),
    path("admin/cms/leads/", views_admin.leads_admin_list, name="leads_list"),
    path("admin/cms/leads/<int:pk>/", views_admin.lead_admin_detail_update, name="lead_detail"),
    path("admin/cms/leads/newsletter/export/", views_admin.export_newsletter_subscribers, name="newsletter_export"),
    path("admin/cms/media/", views_admin.media_library_view, name="media_library"),
    path("admin/cms/media/<int:pk>/delete/", views_admin.media_asset_delete, name="media_delete"),
    path("admin/cms/navigation-footer/", views_admin.navigation_footer_admin, name="navigation_footer_admin"),
    path("admin/cms/seo/", views_admin.seo_settings_admin, name="seo_settings_admin"),
    path("admin/cms/site-settings/", views_admin.site_settings_admin, name="site_settings_admin"),
    path("admin/cms/audit-logs/", views_admin.audit_logs_view, name="audit_logs"),
    path("admin/cms/search/", views_admin.universal_search_view, name="universal_search"),
    path("admin/cms/users/", views_admin.user_permissions_admin, name="user_permissions"),
    path("admin/cms/preview/<str:content_type>/<str:slug_or_id>/", views_admin.draft_preview_view, name="draft_preview"),

    # Public Website Routes
    path("services/", views_public.services_index, name="services_index"),
    path("services/<slug:slug>/", views_public.service_detail, name="service_detail"),
    path("projects/", views_public.projects_index, name="projects_index"),
    path("projects/<slug:slug>/", views_public.project_detail, name="project_detail"),
    path("blog/", views_public.blog_index, name="blog_index"),
    path("blog/<slug:slug>/", views_public.blog_detail, name="blog_detail"),
    path("about/", views_public.about_us, name="about"),
    path("contact/", views_public.contact_us, name="contact"),
    path("legal/<slug:slug>/", views_public.legal_page_detail, name="legal_detail"),
    path("newsletter/subscribe/", views_public.newsletter_subscribe, name="newsletter_subscribe"),
    path("newsletter/unsubscribe/<str:token>/", views_public.newsletter_unsubscribe, name="newsletter_unsubscribe"),
]
