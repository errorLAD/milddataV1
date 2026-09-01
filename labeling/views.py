import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import QuoteRequestForm

logger = logging.getLogger(__name__)


def home(request):
    if request.method == "POST":
        form = QuoteRequestForm(request.POST)
        if form.is_valid():
            quote = form.save()
            _send_quote_notification(quote)
            messages.success(
                request,
                "Thank you! Your quote request has been submitted. "
                "We'll get back to you within 1–2 business days.",
            )
            return redirect("labeling:home")
    else:
        form = QuoteRequestForm()

    return render(request, "labeling/home.html", {"form": form})


def _send_quote_notification(quote):
    subject = f"New Quote Request — {quote.company_name}"
    body = (
        f"Company: {quote.company_name}\n"
        f"Email: {quote.email}\n"
        f"Data Type: {quote.get_data_type_display()}\n"
        f"Volume: {quote.volume}\n"
        f"Timeline: {quote.timeline}\n"
        f"Message:\n{quote.message or '(none)'}\n"
    )
    recipient = settings.QUOTE_NOTIFICATION_EMAIL
    if not recipient or not settings.EMAIL_HOST_USER:
        logger.warning(
            "Email not configured — quote request saved but notification skipped."
        )
        return
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send quote notification email")
