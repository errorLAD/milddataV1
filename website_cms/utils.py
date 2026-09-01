import re
from django.shortcuts import redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied


ALLOWED_TAGS = [
    "p", "b", "i", "u", "strong", "em", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "a", "img", "blockquote", "code", "pre", "table", "thead",
    "tbody", "tr", "th", "td", "span", "div", "br", "hr", "sub", "sup"
]

ALLOWED_ATTRS = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height", "class"],
    "div": ["class", "style"],
    "span": ["class", "style"],
    "p": ["class", "style"],
    "*": ["class"]
}


def sanitize_html(html_content):
    """
    Sanitize rich text HTML input to prevent XSS while allowing standard web markup.
    Strips script, iframe, onload, onclick, javascript: URIs, etc.
    """
    if not html_content:
        return ""

    # Remove script tags and contents
    cleaned = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", html_content, flags=re.IGNORECASE)
    # Remove iframe tags
    cleaned = re.sub(r"<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>", "", cleaned, flags=re.IGNORECASE)
    # Remove event handlers (onload, onclick, etc.)
    cleaned = re.sub(r"\s*on\w+\s*=\s*['\"].*?['\"]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*on\w+\s*=\s*[^\s>]+", "", cleaned, flags=re.IGNORECASE)
    # Strip dangerous javascript: links
    cleaned = re.sub(r'href\s*=\s*["\']?\s*javascript:[^"\'>]*["\']?', 'href="#"', cleaned, flags=re.IGNORECASE)

    return cleaned


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def check_cms_permission(user, permission_type="view"):
    """
    Check if user is authorized to access CMS admin.
    Superusers and staff automatically have full access.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True

    # Check custom UserPermissionRole
    if hasattr(user, "cms_role"):
        role = user.cms_role
        if permission_type == "publish" and not role.can_publish:
            return False
        if permission_type == "delete" and not role.can_delete:
            return False
        if permission_type == "settings" and not role.can_manage_settings:
            return False
        return True

    return False


def require_cms_admin(permission_type="view"):
    """Decorator for CMS views to enforce permissions."""
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                admin_login_url = reverse("website_cms:admin_login")
                return redirect(f"{admin_login_url}?next={request.path}")

            if not check_cms_permission(request.user, permission_type):
                raise PermissionDenied("You do not have administrative permission to access this area.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
