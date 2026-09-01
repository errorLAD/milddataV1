import logging
import socket
from decimal import Decimal
from urllib.parse import urlparse

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import DemoLead, Order, Product
from .saas_registry import SAAS_PRODUCTS, SLUG_ALIASES, get_all_saas_products, get_saas_product, resolve_saas_url

logger = logging.getLogger(__name__)


def _get_razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def _is_url_reachable(url, timeout=0.15):
    """Fast check if a target URL host and port are accepting TCP connections."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def catalog(request):
    category = request.GET.get("category", "")
    currency = getattr(request, "currency", request.session.get("currency", "INR"))
    billing_cycle = request.session.get("billing_cycle", "monthly")
    
    if Product.objects.count() == 0:
        for slug, item in SAAS_PRODUCTS.items():
            Product.objects.get_or_create(
                name=item["name"],
                defaults={
                    "description": item["description"],
                    "category": item["category_code"],
                    "price_inr_monthly": item["price_inr_monthly"],
                    "price_inr_yearly": item["price_inr_yearly"],
                    "price_usd_monthly": item["price_usd_monthly"],
                    "price_usd_yearly": item["price_usd_yearly"],
                    "features": "\n".join([f"{f['title']}: {f['desc']}" for f in item.get("features", [])]),
                    "is_active": True,
                },
            )

    products = Product.objects.filter(is_active=True)
    if category in ("ai_agent", "saas_tool"):
        products = products.filter(category=category)

    # Attach computed regional prices to product objects
    for p in products:
        p.active_display_price = p.get_display_price(currency=currency, billing_cycle=billing_cycle)
        p.active_price_amount = p.get_price_amount(currency=currency, billing_cycle=billing_cycle)

    saas_products = get_all_saas_products(category=category, currency=currency, billing_cycle=billing_cycle)
    if not saas_products:
        saas_products = get_all_saas_products(currency=currency, billing_cycle=billing_cycle)

    return render(
        request,
        "products/catalog.html",
        {
            "products": products,
            "saas_products": saas_products,
            "active_category": category,
        },
    )


def saas_directory(request):
    category = request.GET.get("category", "")
    query = request.GET.get("q", "").strip().lower()
    currency = getattr(request, "currency", request.session.get("currency", "INR"))
    billing_cycle = request.session.get("billing_cycle", "monthly")

    products = get_all_saas_products(currency=currency, billing_cycle=billing_cycle)

    if category:
        products = [p for p in products if p["category_code"] == category or p["category"].lower() == category.lower()]

    if query:
        products = [
            p for p in products 
            if query in p["name"].lower() or query in p["description"].lower() or query in p["category"].lower()
        ]

    return render(
        request,
        "products/saas_directory.html",
        {
            "products": products,
            "active_category": category,
            "search_query": query,
        },
    )


def saas_detail(request, slug):
    target_slug = SLUG_ALIASES.get(slug.lower(), slug)
    product = get_saas_product(target_slug)
    if not product:
        # Fallback check if identifier is numeric or db product
        if slug.isdigit():
            return product_detail(request, pk=int(slug))
        raise Http404("SaaS product not found.")

    region = getattr(request, "region", request.session.get("region", "IN"))
    currency = getattr(request, "currency", request.session.get("currency", "INR" if region == "IN" else "USD"))
    billing_cycle = request.GET.get("billing") or request.session.get("billing_cycle", "monthly")
    if billing_cycle in ("monthly", "yearly"):
        request.session["billing_cycle"] = billing_cycle

    target_url = resolve_saas_url(target_slug)

    # Get or create database Product record to allow instant checkout
    db_product, _ = Product.objects.get_or_create(
        name=product["name"],
        defaults={
            "category": "saas_tool",
            "description": product["description"],
            "price_inr_monthly": Decimal("199.00"),
            "price_inr_yearly": Decimal("1982.00"),
            "price_usd_monthly": Decimal("5.00"),
            "price_usd_yearly": Decimal("49.80"),
            "billing_type": "monthly",
            "is_active": True,
        }
    )

    # Compute exact prices and crossed-out values
    if currency == "USD":
        monthly_price_str = "$5/mo"
        yearly_price_str = "$49.80/yr"
        yearly_original_str = "$60.00"
        display_price = "$49.80/yr" if billing_cycle == "yearly" else "$5/mo"
        price_amount = Decimal("49.80") if billing_cycle == "yearly" else Decimal("5.00")
        tax_label = "Standard Tax Excluded"
        tax_amount = Decimal("0.00")
        total_amount = price_amount
        currency_symbol = "$"
    else:
        monthly_price_str = "₹199/mo"
        yearly_price_str = "₹1,982/yr"
        yearly_original_str = "₹2,388"
        display_price = "₹1,982/yr" if billing_cycle == "yearly" else "₹199/mo"
        price_amount = Decimal("1982.00") if billing_cycle == "yearly" else Decimal("199.00")
        tax_label = "GST 18%"
        tax_amount = (price_amount * Decimal("18.00")) / Decimal("100.00")
        total_amount = price_amount + tax_amount
        currency_symbol = "₹"

    features_list = product.get("features", [
        {"title": "Cloud Enterprise SaaS Platform", "desc": "Hosted infrastructure with high availability."},
        {"title": "Role-Based Multi-User Control", "desc": "Granular permissions for team members."},
        {"title": "Automated Notifications", "desc": "Instant alerts via email and SMS."},
        {"title": "Enterprise Security", "desc": "256-bit SSL and data encryption."},
        {"title": "Real-Time Analytics", "desc": "Custom reporting and visual dashboards."},
        {"title": "Priority Support", "desc": "24/7 email, chat, and ticketing."},
    ])

    dashboard_stats = product.get("dashboard_stats", {
        "stat1_label": "Active Users", "stat1_val": "24",
        "stat2_label": "Operations Done", "stat2_val": "48",
        "stat3_label": "Monthly Volume", "stat3_val": "₹2,45,000",
        "stat4_label": "Efficiency", "stat4_val": "92%",
    })

    benefits = product.get("benefits", [
        "Easy to use and quick to set up in 5 minutes",
        "Automated workflows and instant alerts",
        "Secure, 256-bit encrypted cloud platform",
        "Access from anywhere on desktop, tablet, and mobile",
        "Regular updates and dedicated email & chat support",
        "Built for target business workflow optimization",
    ])

    faqs = [
        {
            "q": f"What is {product['name']}?",
            "a": f"{product['name']} is an enterprise cloud SaaS platform designed to automate {product['description'].lower()}"
        },
        {
            "q": "Who is this product for?",
            "a": "It is built for business owners, department managers, operations leads, and enterprise teams looking for digital workflow control."
        },
        {
            "q": "Is there a free trial?",
            "a": "Yes! You can start with our 7-day free trial with no credit card required to explore the entire platform."
        },
        {
            "q": "Do I need a credit card to get started?",
            "a": "No credit card is required to launch your free trial or test drive live application demos."
        },
        {
            "q": "Can I cancel or upgrade anytime?",
            "a": "Yes! You can upgrade from monthly to yearly plans or cancel your subscription anytime with one click."
        },
        {
            "q": "What support is included?",
            "a": f"All plans include email, live chat, ticket support, and automated documentation from the {product.get('developer', 'Milda Data')} engineering team."
        },
        {
            "q": "Is my data secure?",
            "a": "Yes, all data is protected using 256-bit SSL encryption, automated backups, and strict data privacy compliance."
        },
    ]

    canonical_url = request.build_absolute_uri(reverse("products:saas_detail", kwargs={"slug": target_slug}))

    return render(
        request,
        "products/saas_detail.html",
        {
            "product": product,
            "db_product": db_product,
            "target_url": target_url,
            "active_region": region,
            "active_currency": currency,
            "currency_symbol": currency_symbol,
            "billing_cycle": billing_cycle,
            "monthly_price_str": monthly_price_str,
            "yearly_price_str": yearly_price_str,
            "yearly_original_str": yearly_original_str,
            "display_price": display_price,
            "price_amount": price_amount,
            "tax_label": tax_label,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "features_list": features_list,
            "dashboard_stats": dashboard_stats,
            "benefits": benefits,
            "faqs": faqs,
            "canonical_url": canonical_url,
        },
    )


def universal_product_detail(request, identifier):
    """
    Universal routing handler for /products/detail/<identifier>
    Supports numeric database product IDs (e.g. 1) and string SaaS slugs (e.g. propflow, udhaar, stockflow).
    """
    if identifier.isdigit():
        return product_detail(request, pk=int(identifier))
    return saas_detail(request, slug=identifier)


def saas_launch(request, slug):
    target_slug = SLUG_ALIASES.get(slug.lower(), slug)
    product = get_saas_product(target_slug)
    if not product or product.get("status") != "active":
        raise Http404("Product is not available or not configured.")

    # Auto-enable guest mode in session so guest mode works seamlessly without requiring login
    request.session["is_guest"] = True

    target_url = resolve_saas_url(target_slug)
    if not target_url:
        raise Http404("Application endpoint is not properly configured.")

    # Verify if target service port is reachable locally before redirecting
    if not _is_url_reachable(target_url):
        parsed = urlparse(target_url)
        port = parsed.port or 8000
        folder = product.get("folder_name", "")

        run_cmd = f"python {folder}/manage.py runserver {port}"
        if "part1" in str(folder).lower() or folder in ("buinessslite", "fleetmangment", "machinelite", "propertylite", "Inventory + Purchasing"):
            if folder == "buinessslite":
                run_cmd = "python buinessslite/part1buinesslite/manage.py runserver 8003"
            elif folder == "fleetmangment":
                run_cmd = "python fleetmangment/part1fleetmagment/manage.py runserver 8004"
            elif folder == "Inventory + Purchasing":
                run_cmd = 'python "Inventory + Purchasing/part1InventoryPurchasing/manage.py" runserver 8005'
            elif folder == "machinelite":
                run_cmd = "python machinelite/part1machinelite/manage.py runserver 8006"
            elif folder == "propertylite":
                run_cmd = "python propertylite/part1propertylite/manage.py runserver 8007"

        return render(
            request,
            "products/saas_offline.html",
            {
                "product": product,
                "target_url": target_url,
                "run_cmd": run_cmd,
            },
            status=503,
        )

    return redirect(target_url)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)

    # Check if this database product maps to a registered SaaS product
    if request.method == "GET":
        for slug_key, saas_item in SAAS_PRODUCTS.items():
            if saas_item["name"].lower() in product.name.lower() or product.name.lower() in saas_item["name"].lower():
                return saas_detail(request, slug=slug_key)

    razorpay_order = None
    order = None
    customer_email = request.user.email if request.user.is_authenticated else ""

    region = getattr(request, "region", request.session.get("region", "IN"))
    currency = getattr(request, "currency", request.session.get("currency", "INR" if region == "IN" else "USD"))
    billing_cycle = request.POST.get("billing_cycle") or request.GET.get("billing") or request.session.get("billing_cycle", "monthly")

    # Authoritative server-side price & tax calculation
    subtotal, tax_amount, total_amount, tax_rate = product.get_tax_breakdown(currency=currency, billing_cycle=billing_cycle)
    display_price = product.get_display_price(currency=currency, billing_cycle=billing_cycle)

    if request.method == "POST":
        customer_email = request.POST.get("email", customer_email)
        if customer_email:
            order = Order.objects.create(
                product=product,
                user=request.user if request.user.is_authenticated else None,
                customer_email=customer_email,
                region=region,
                currency=currency,
                billing_cycle=billing_cycle,
                subtotal_amount=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                payment_status="pending",
            )
            try:
                client = _get_razorpay_client()
                amount_in_subunits = int(total_amount * 100)
                razorpay_order = client.order.create(
                    {
                        "amount": amount_in_subunits,
                        "currency": currency,
                        "receipt": f"order_{order.pk}",
                        "notes": {
                            "product_id": str(product.pk),
                            "order_id": str(order.pk),
                            "customer_email": customer_email,
                            "currency": currency,
                            "billing_cycle": billing_cycle,
                        },
                    }
                )
                order.razorpay_order_id = razorpay_order["id"]
                order.save()
            except Exception as e:
                messages.error(request, f"Payment initialization failed: {e}")

    return render(
        request,
        "products/detail.html",
        {
            "product": product,
            "razorpay_order_id": razorpay_order["id"] if razorpay_order else "",
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "amount_in_subunits": int(total_amount * 100) if order else 0,
            "order": order,
            "customer_email": customer_email,
            "region": region,
            "currency": currency,
            "billing_cycle": billing_cycle,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "tax_rate": tax_rate,
            "display_price": display_price,
        },
    )


@login_required
@require_POST
def payment_verify(request):
    razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    razorpay_signature = request.POST.get("razorpay_signature", "")

    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        return HttpResponseBadRequest("Missing payment parameters.")

    order = get_object_or_404(
        Order,
        razorpay_order_id=razorpay_order_id,
        user=request.user,
    )

    try:
        client = _get_razorpay_client()
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )
    except razorpay.errors.SignatureVerificationError:
        order.payment_status = "failed"
        order.save(update_fields=["payment_status"])
        messages.error(request, "Payment verification failed. Please contact support.")
        return redirect("products:detail", pk=order.product.pk)
    except Exception:
        logger.exception("Payment verification error")
        messages.error(request, "An error occurred during payment verification.")
        return redirect("products:detail", pk=order.product.pk)

    order.razorpay_payment_id = razorpay_payment_id
    order.payment_status = "paid"
    order.save(update_fields=["razorpay_payment_id", "payment_status"])

    request.session["last_paid_order_id"] = order.pk
    return redirect("products:success")


@login_required
def payment_success(request):
    order_id = request.session.pop("last_paid_order_id", None)
    if not order_id:
        return redirect("products:catalog")
    order = get_object_or_404(
        Order,
        pk=order_id,
        payment_status="paid",
        user=request.user,
    )
    return render(request, "products/success.html", {"order": order})



@csrf_exempt
@require_POST
def book_demo(request):
    full_name = request.POST.get("full_name", "").strip()
    email = request.POST.get("email", "").strip()
    phone = request.POST.get("phone", "").strip()
    place = request.POST.get("place", "").strip()
    product_name = request.POST.get("product_name", "").strip() or "General SaaS Application"
    notes = request.POST.get("notes", "").strip()

    if not full_name or not email or not phone or not place:
        return JsonResponse(
            {"success": False, "error": "Please fill in all required fields (Name, Email, Phone, and Location)."},
            status=400,
        )

    # Save lead record to database
    lead = DemoLead.objects.create(
        product_name=product_name,
        full_name=full_name,
        email=email,
        phone=phone,
        place=place,
        notes=notes,
    )

    try:
        from website_cms.models import ContactLead
        ContactLead.objects.create(
            lead_type="demo",
            name=full_name,
            email=email,
            phone=phone,
            company=place,
            message=notes or f"Location / City: {place}",
            product_or_service=product_name,
            source_page="Product Page Demo Modal",
        )
    except Exception:
        pass

    # Primary recipient requested by user: ab.mishra@yahoo.com
    recipients = ["ab.mishra@yahoo.com"]
    fallback_email = getattr(settings, "QUOTE_NOTIFICATION_EMAIL", "") or getattr(settings, "DEFAULT_FROM_EMAIL", "")
    if fallback_email and fallback_email not in recipients:
        recipients.append(fallback_email)

    subject = f"[Demo Interest Lead] {product_name} - {full_name} ({place})"
    message_body = (
        f"New Live Demo / Interest Lead Received!\n\n"
        f"Target Product Interested In: {product_name}\n"
        f"Full Name: {full_name}\n"
        f"Email Address: {email}\n"
        f"Phone / WhatsApp: {phone}\n"
        f"Location / Place: {place}\n\n"
        f"Additional Business Requirements / Notes:\n"
        f"{notes or 'None provided.'}\n\n"
        f"Submitted At: {lead.created_at.strftime('%Y-%m-%d %H:%M:%S IST')}\n"
        f"---\n"
        f"Milda Data Enterprise Lead Notification System"
    )

    try:
        send_mail(
            subject=subject,
            message=message_body,
            from_email=settings.DEFAULT_FROM_EMAIL or "noreply@mildadata.com",
            recipient_list=recipients,
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Failed to send demo lead email: {e}")

    return JsonResponse({
        "success": True,
        "message": f"Thank you {full_name}! Your demo request for {product_name} has been sent to our sales team (ab.mishra@yahoo.com). We will reach out shortly."
    })
