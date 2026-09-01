# Mithila AI Website

Django website for **Mithila AI** — offering B2B data labeling services and a self-serve product catalog for AI agents and SaaS tools.

## Features

- **Homepage** — two clear paths: data labeling (quote-based) and product catalog (checkout)
- **Labeling app** — landing page with contact/quote form, email notifications, Django admin
- **Products app** — catalog with category filters, product detail, Razorpay checkout, order tracking via admin
- **Accounts** — sign up / log in required before purchasing products

## Setup

```bash
# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Copy environment config
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux

# Edit .env with your SECRET_KEY, email, and Razorpay credentials

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit http://127.0.0.1:8000/

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for development |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `EMAIL_HOST` | SMTP server (e.g. `smtp.gmail.com`) |
| `EMAIL_PORT` | SMTP port (default `587`) |
| `EMAIL_USE_TLS` | Enable TLS (`True`) |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password / app password |
| `DEFAULT_FROM_EMAIL` | Sender address |
| `QUOTE_NOTIFICATION_EMAIL` | Where quote requests are sent |
| `RAZORPAY_KEY_ID` | Razorpay API key ID |
| `RAZORPAY_KEY_SECRET` | Razorpay API secret |

## Purchasing Flow

1. Browse products at `/products/` (no account needed).
2. **Sign up** at `/accounts/signup/` or **log in** at `/accounts/login/`.
3. Open a product and click **Proceed to Payment**.
4. Complete Razorpay checkout.
5. View purchased products anytime at `/products/my-orders/`.

## Admin

Manage products, orders, and quote requests at `/admin/`.

Add products via admin with category (`AI Agent` / `SaaS Tool`), price, billing type, and optional access info shown after payment.

## Project Structure

```
mithila_ai/          # Project settings & root URLs
labeling/            # B2B data labeling (quote requests)
products/            # Product catalog & Razorpay checkout
templates/           # Global templates (base.html, home.html)
static/css/          # Stylesheet
```

## Razorpay Testing

Use [Razorpay test keys](https://razorpay.com/docs/payments/payments/test-card-details/) for development. After adding a product in admin, go to the catalog, click Buy, enter an email, and complete test checkout.
