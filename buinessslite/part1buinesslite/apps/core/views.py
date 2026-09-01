from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json

from apps.core.models import Organization, UserProfile, AuditLog, Notification, NotificationType, UserRole
from apps.core.ai_engine import process_ai_request
from apps.sales.models import Invoice, InvoiceItem, Customer, Quote, SalesOrder, Payment, InvoiceStatus
from apps.inventory.models import Product, StockMovement, ProductType, Warehouse
from apps.purchasing.models import Supplier, PurchaseOrder, POStatus
from apps.finance.models import Expense, ExpenseCategory
from apps.people.models import Employee, Attendance, AttendanceStatus, EmployeeDocument, LeaveRequest, SalaryPayment
from apps.operations.models import Task, TaskStatus, BusinessDocument, CalendarEvent

COUNTRY_PRESETS = {
    "India": {"code": "INR", "symbol": "₹", "tax_name": "GST", "tax_rate": 18.0},
    "United States": {"code": "USD", "symbol": "$", "tax_name": "Sales Tax", "tax_rate": 10.0},
    "United Kingdom": {"code": "GBP", "symbol": "£", "tax_name": "VAT", "tax_rate": 20.0},
    "Germany": {"code": "EUR", "symbol": "€", "tax_name": "VAT", "tax_rate": 19.0},
    "France": {"code": "EUR", "symbol": "€", "tax_name": "TVA", "tax_rate": 20.0},
    "Canada": {"code": "CAD", "symbol": "C$", "tax_name": "GST/HST", "tax_rate": 13.0},
    "Australia": {"code": "AUD", "symbol": "A$", "tax_name": "GST", "tax_rate": 10.0},
    "Japan": {"code": "JPY", "symbol": "¥", "tax_name": "Consumption Tax", "tax_rate": 10.0},
    "United Arab Emirates": {"code": "AED", "symbol": "AED", "tax_name": "VAT", "tax_rate": 5.0},
    "Singapore": {"code": "SGD", "symbol": "S$", "tax_name": "GST", "tax_rate": 9.0},
}

from django.contrib.auth.models import User

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def guest_login_view(request):
    guest_user, _ = User.objects.get_or_create(
        username="guest_demo",
        defaults={'email': "guest@milddata.com", 'first_name': "Guest", 'last_name': "Explorer"}
    )
    if not guest_user.has_usable_password():
        guest_user.set_password("guest_demo_123")
        guest_user.save()

    org = Organization.objects.first()
    if org:
        UserProfile.objects.get_or_create(
            user=guest_user,
            defaults={'organization': org, 'role': UserRole.VIEWER}
        )

    login(request, guest_user)
    request.session['is_guest'] = True
    request.session.set_expiry(3600)

    if org:
        AuditLog.objects.create(
            organization=org, user=guest_user, action="Guest Session Started",
            model_name="UserProfile", record_id=str(guest_user.id),
            details="Temporary guest session initiated."
        )
    return redirect('dashboard')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    org = request.organization

    today = timezone.now().date()
    start_30_days = today - timedelta(days=30)

    # 1. Financial Metrics (30d)
    sales_total = Invoice.objects.filter(organization=org, date__gte=start_30_days).exclude(status=InvoiceStatus.VOID).aggregate(total=Sum('total_amount'))['total'] or 0.00
    expense_total = Expense.objects.filter(organization=org, date__gte=start_30_days).aggregate(total=Sum('amount'))['total'] or 0.00
    salary_total_30d = SalaryPayment.objects.filter(organization=org, payment_date__gte=start_30_days).aggregate(total=Sum('amount'))['total'] or 0.00
    
    pos_total = PurchaseOrder.objects.filter(organization=org, date__gte=start_30_days).exclude(status=POStatus.CANCELLED).aggregate(total=Sum('total_amount'))['total'] or 0.00
    gross_profit = float(sales_total) - float(pos_total)
    estimated_profit = gross_profit - float(expense_total)

    # Outstanding Invoices & Payables
    unpaid_invoices = Invoice.objects.filter(organization=org).exclude(status__in=[InvoiceStatus.PAID, InvoiceStatus.VOID])
    outstanding_total = sum(inv.remaining_amount for inv in unpaid_invoices)
    
    pending_pos = PurchaseOrder.objects.filter(organization=org).exclude(status__in=[POStatus.COMPLETED, POStatus.CANCELLED])
    payables_total = sum(po.total_amount for po in pending_pos)

    # Inventory Valuation & Low Stock
    physical_products = Product.objects.filter(organization=org, product_type=ProductType.PHYSICAL)
    inventory_value = sum(p.stock_quantity * p.purchase_price for p in physical_products)
    low_stock_count = len([p for p in physical_products if p.is_low_stock])
    out_of_stock_count = physical_products.filter(stock_quantity__lte=0).count()

    # Employee & Attendance Summary
    employees = Employee.objects.filter(organization=org, status='ACTIVE')
    employee_count = employees.count()
    
    today_attendances = Attendance.objects.filter(organization=org, date=today)
    present_count = today_attendances.filter(status__in=[AttendanceStatus.PRESENT, AttendanceStatus.REMOTE, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]).count()
    today_absent_count = today_attendances.filter(status=AttendanceStatus.ABSENT).count()

    # Top 5 Customers by Revenue
    cust_revenue = {}
    for inv in Invoice.objects.filter(organization=org).exclude(status=InvoiceStatus.VOID):
        name = inv.customer.company_name
        cust_revenue[name] = cust_revenue.get(name, 0.0) + float(inv.total_amount)
    top_customers = sorted(cust_revenue.items(), key=lambda x: x[1], reverse=True)[:5]

    # Top 5 Best-Selling Products
    prod_sales = {}
    for item in InvoiceItem.objects.filter(invoice__organization=org).exclude(invoice__status=InvoiceStatus.VOID):
        if item.product:
            pname = item.product.name
            prod_sales[pname] = prod_sales.get(pname, {'qty': 0, 'revenue': 0.0})
            prod_sales[pname]['qty'] += item.quantity
            prod_sales[pname]['revenue'] += float(item.line_total)
    top_products = sorted(prod_sales.items(), key=lambda x: x[1]['revenue'], reverse=True)[:5]

    # Needs Attention Actionable Alerts
    overdue_invoices_count = Invoice.objects.filter(organization=org, due_date__lt=today).exclude(status__in=[InvoiceStatus.PAID, InvoiceStatus.VOID]).count()
    pending_po_count = PurchaseOrder.objects.filter(organization=org, status=POStatus.DRAFT).count()
    
    expiring_docs_count = EmployeeDocument.objects.filter(organization=org, expiry_date__lte=today + timedelta(days=30), expiry_date__gte=today).count() + \
                          BusinessDocument.objects.filter(organization=org, expiry_date__lte=today + timedelta(days=30), expiry_date__gte=today).count()

    needs_attention = [
        {'title': f'{overdue_invoices_count} invoices overdue', 'url': '/finance/receivables/', 'type': 'danger', 'count': overdue_invoices_count},
        {'title': f'{low_stock_count} products low in stock', 'url': '/inventory/products/?filter=low_stock', 'type': 'warning', 'count': low_stock_count},
        {'title': f'{today_absent_count} employees absent today', 'url': '/people/attendance/', 'type': 'info', 'count': today_absent_count},
        {'title': f'{pending_po_count} purchase orders pending', 'url': '/purchasing/orders/', 'type': 'warning', 'count': pending_po_count},
        {'title': f'{expiring_docs_count} documents expiring soon', 'url': '/operations/documents/', 'type': 'info', 'count': expiring_docs_count},
    ]
    needs_attention = [item for item in needs_attention if item['count'] > 0]

    recent_activity = AuditLog.objects.filter(organization=org)[:10]

    context = {
        'sales_total': float(sales_total),
        'expense_total': float(expense_total),
        'salary_total_30d': float(salary_total_30d),
        'estimated_profit': float(estimated_profit),
        'outstanding_total': float(outstanding_total),
        'payables_total': float(payables_total),
        'inventory_value': float(inventory_value),
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'employee_count': employee_count,
        'present_count': present_count,
        'today_absent_count': today_absent_count,
        'top_customers': top_customers,
        'top_products': top_products,
        'needs_attention': needs_attention,
        'recent_activity': recent_activity,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def ai_assistant_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get('query', '')
        response_data = process_ai_request(query, request.user_profile, request.organization)
        return JsonResponse(response_data)
    return JsonResponse({'error': 'POST required'}, status=400)

@login_required
def global_search_api(request):
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'results': []})

    org = request.organization
    results = []

    # Customers
    customers = Customer.objects.filter(organization=org, company_name__icontains=q)[:3]
    for c in customers:
        results.append({'category': 'Customer', 'title': c.company_name, 'sub': c.email or c.phone, 'url': f'/sales/customers/{c.id}/'})

    # Suppliers
    suppliers = Supplier.objects.filter(organization=org, company_name__icontains=q)[:3]
    for s in suppliers:
        results.append({'category': 'Supplier', 'title': s.company_name, 'sub': s.email or s.phone, 'url': f'/purchasing/suppliers/{s.id}/'})

    # Products
    products = Product.objects.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(barcode__icontains=q), organization=org)[:3]
    for p in products:
        results.append({'category': 'Product', 'title': p.name, 'sub': f"SKU: {p.sku} • Stock: {p.stock_quantity}", 'url': f'/inventory/products/{p.id}/'})

    # Invoices
    invoices = Invoice.objects.filter(Q(invoice_number__icontains=q) | Q(customer__company_name__icontains=q), organization=org)[:3]
    for inv in invoices:
        results.append({'category': 'Invoice', 'title': inv.invoice_number, 'sub': f"{inv.customer.company_name} • {org.currency_symbol}{inv.total_amount}", 'url': f'/sales/invoices/{inv.id}/'})

    # Employees
    employees = Employee.objects.filter(organization=org, name__icontains=q)[:3]
    for e in employees:
        results.append({'category': 'Employee', 'title': e.name, 'sub': e.job_title, 'url': f'/people/employees/{e.id}/'})

    # Tasks
    tasks = Task.objects.filter(organization=org, title__icontains=q)[:3]
    for t in tasks:
        results.append({'category': 'Task', 'title': t.title, 'sub': f"Status: {t.status}", 'url': '/operations/tasks/'})

    return JsonResponse({'results': results})

@login_required
def notifications_view(request):
    org = request.organization
    notifications = Notification.objects.filter(organization=org)
    return render(request, 'core/notifications.html', {'notifications': notifications})

@login_required
@require_POST
def mark_notification_read_api(request, notif_id):
    org = request.organization
    notif = get_object_or_404(Notification, id=notif_id, organization=org)
    notif.is_read = True
    notif.save()
    return JsonResponse({'success': True})

@login_required
def settings_view(request):
    org = request.organization
    if request.method == 'POST':
        selected_country = request.POST.get('country', org.country)
        org.country = selected_country
        
        # Check if country preset exists
        if selected_country in COUNTRY_PRESETS and 'auto_preset' in request.POST:
            preset = COUNTRY_PRESETS[selected_country]
            org.currency_code = preset['code']
            org.currency_symbol = preset['symbol']
            org.tax_name = preset['tax_name']
            org.tax_rate = preset['tax_rate']
        else:
            org.currency_code = request.POST.get('currency_code', org.currency_code)
            org.currency_symbol = request.POST.get('currency_symbol', org.currency_symbol)
            org.tax_name = request.POST.get('tax_name', org.tax_name)
            org.tax_rate = float(request.POST.get('tax_rate', org.tax_rate))

        org.name = request.POST.get('name', org.name)
        org.timezone = request.POST.get('timezone', org.timezone)
        org.tax_inclusive = request.POST.get('tax_inclusive') == 'on'
        org.invoice_prefix = request.POST.get('invoice_prefix', org.invoice_prefix)
        org.save()

        # Audit log
        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action="Settings Updated",
            model_name="Organization",
            record_id=str(org.id),
            details=f"Country updated to {org.country} ({org.currency_symbol} {org.currency_code})."
        )
        return redirect('settings')

    return render(request, 'core/settings.html', {
        'org': org,
        'country_presets': COUNTRY_PRESETS
    })

@login_required
def quick_switch_country_api(request):
    if request.method == 'POST':
        org = request.organization
        data = json.loads(request.body)
        c_name = data.get('country')
        if c_name in COUNTRY_PRESETS:
            preset = COUNTRY_PRESETS[c_name]
            org.country = c_name
            org.currency_code = preset['code']
            org.currency_symbol = preset['symbol']
            org.tax_name = preset['tax_name']
            org.tax_rate = preset['tax_rate']
            org.save()

            AuditLog.objects.create(
                organization=org, user=request.user, action="Country Switched",
                model_name="Organization", record_id=str(org.id),
                details=f"Country switched to {c_name} ({preset['symbol']} {preset['code']})."
            )
            return JsonResponse({'success': True, 'currency_symbol': preset['symbol'], 'currency_code': preset['code']})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def audit_log_view(request):
    org = request.organization
    logs = AuditLog.objects.filter(organization=org)
    return render(request, 'core/audit_log.html', {'logs': logs})

def pwa_manifest_view(request):
    manifest_data = {
        "name": "MildData BusinessLite",
        "short_name": "MildData",
        "description": "Simple All-in-One Operating System for Small Businesses",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#F7F8FA",
        "theme_color": "#2451FF",
        "icons": [
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return JsonResponse(manifest_data)

def pwa_sw_view(request):
    sw_code = """
    const CACHE_NAME = 'businesslite-v1';
    const urlsToCache = ['/', '/static/css/karobar.css'];

    self.addEventListener('install', event => {
        event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)));
    });

    self.addEventListener('fetch', event => {
        event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
    });
    """
    return HttpResponse(sw_code, content_type='application/javascript')
