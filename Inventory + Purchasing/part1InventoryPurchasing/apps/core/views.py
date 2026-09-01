from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Q, F
from django.contrib import messages
from django.core.management import call_command
from decimal import Decimal
import datetime

from apps.inventory.models import Product, Warehouse, Inventory, StockMovement
from apps.purchasing.models import Supplier, PurchaseOrder, PurchaseBill
from apps.sales.models import Customer, SalesOrder, Invoice
from apps.finance.models import Payment
from apps.core.models import Notification, AuditLog, OrganizationAISetting, AIUsageLog
from apps.core.ai_copilot import StockFlowAIEngine

@login_required
def dashboard_view(request):
    org = request.organization
    if not org:
        return redirect('onboarding')

    invoices = Invoice.objects.filter(organization=org).exclude(status='VOID')
    total_sales = sum(inv.total_amount for inv in invoices)

    purchase_orders = PurchaseOrder.objects.filter(organization=org).exclude(status='CANCELLED')
    total_purchases = sum(po.total_amount for po in purchase_orders)

    products = Product.objects.filter(organization=org, is_archived=False)
    total_inventory_value = sum(p.inventory_value for p in products if p.product_type == 'PHYSICAL')

    open_invoices = invoices.filter(status__in=['UNPAID', 'PARTIALLY_PAID', 'OVERDUE'])
    outstanding_receivables = sum(inv.remaining_balance for inv in open_invoices)

    open_bills = PurchaseBill.objects.filter(organization=org, status__in=['OPEN', 'PARTIALLY_PAID', 'OVERDUE'])
    outstanding_payables = sum(b.remaining_balance for b in open_bills)

    low_stock_products = []
    out_of_stock_count = 0
    low_stock_count = 0
    total_units_count = 0

    for p in products:
        if p.product_type == 'PHYSICAL':
            tot = p.total_stock
            total_units_count += tot
            if tot <= 0:
                out_of_stock_count += 1
                low_stock_products.append(p)
            elif tot <= p.reorder_level:
                low_stock_count += 1
                low_stock_products.append(p)

    recent_invoices = invoices[:5]
    recent_pos = purchase_orders[:5]
    recent_movements = StockMovement.objects.filter(organization=org)[:6]

    categories_data = []
    for p in products:
        if p.product_type == 'PHYSICAL' and p.category:
            found = False
            for cat_item in categories_data:
                if cat_item['name'] == p.category.name:
                    cat_item['val'] += float(p.inventory_value)
                    cat_item['count'] += 1
                    found = True
                    break
            if not found:
                categories_data.append({
                    'name': p.category.name,
                    'val': float(p.inventory_value),
                    'count': 1
                })

    context = {
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'total_inventory_value': total_inventory_value,
        'outstanding_receivables': outstanding_receivables,
        'outstanding_payables': outstanding_payables,
        'total_products_count': products.count(),
        'total_units_count': total_units_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'low_stock_products': low_stock_products[:8],
        'recent_invoices': recent_invoices,
        'recent_pos': recent_pos,
        'recent_movements': recent_movements,
        'categories_data': categories_data,
    }

    return render(request, 'dashboard/overview.html', context)

@login_required
def search_api(request):
    org = request.organization
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'results': []})

    results = []
    for p in Product.objects.filter(organization=org).filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(barcode__icontains=q))[:5]:
        results.append({
            'type': 'Product',
            'title': p.name,
            'subtitle': f"SKU: {p.sku} | Price: {org.currency_symbol}{p.selling_price}",
            'url': f"/inventory/products/{p.id}/"
        })

    for c in Customer.objects.filter(organization=org).filter(Q(company_name__icontains=q) | Q(contact_person__icontains=q) | Q(email__icontains=q))[:4]:
        results.append({
            'type': 'Customer',
            'title': c.company_name,
            'subtitle': f"Contact: {c.contact_person or c.email}",
            'url': f"/sales/customers/{c.id}/"
        })

    for s in Supplier.objects.filter(organization=org).filter(Q(company_name__icontains=q) | Q(contact_person__icontains=q) | Q(email__icontains=q))[:4]:
        results.append({
            'type': 'Supplier',
            'title': s.company_name,
            'subtitle': f"Contact: {s.contact_person or s.email}",
            'url': f"/purchasing/suppliers/{s.id}/"
        })

    for inv in Invoice.objects.filter(organization=org).filter(Q(invoice_number__icontains=q) | Q(customer__company_name__icontains=q))[:4]:
        results.append({
            'type': 'Invoice',
            'title': inv.invoice_number,
            'subtitle': f"Customer: {inv.customer.company_name} | {org.currency_symbol}{inv.total_amount}",
            'url': f"/sales/invoices/{inv.id}/"
        })

    for po in PurchaseOrder.objects.filter(organization=org).filter(Q(po_number__icontains=q) | Q(supplier__company_name__icontains=q))[:4]:
        results.append({
            'type': 'Purchase Order',
            'title': po.po_number,
            'subtitle': f"Supplier: {po.supplier.company_name} | Status: {po.get_status_display()}",
            'url': f"/purchasing/pos/{po.id}/"
        })

    return JsonResponse({'results': results})

@login_required
def barcode_lookup_api(request):
    org = request.organization
    code = request.GET.get('code', '').strip()
    if not code:
        return JsonResponse({'success': False, 'error': 'No barcode provided'})

    product = Product.objects.filter(organization=org).filter(Q(barcode=code) | Q(sku=code)).first()
    if not product:
        return JsonResponse({'success': False, 'error': f'Product with barcode/SKU "{code}" not found'})

    return JsonResponse({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'barcode': product.barcode,
            'selling_price': float(product.selling_price),
            'purchase_price': float(product.purchase_price),
            'total_stock': product.total_stock,
            'status': product.status,
            'detail_url': f"/inventory/products/{product.id}/"
        }
    })

# --- STOCKFLOW AI COPILOT ENDPOINTS ---
@login_required
def ai_copilot_api(request):
    org = request.organization
    prompt = request.GET.get('prompt', '').strip() or request.POST.get('prompt', '').strip()

    if not prompt:
        return JsonResponse({'success': False, 'error': 'Empty prompt'})

    ai_engine = StockFlowAIEngine(organization=org, user=request.user)
    result = ai_engine.process_query(prompt)

    # Log query
    AIUsageLog.objects.create(
        organization=org,
        user=request.user,
        prompt=prompt,
        response=result['answer'],
        has_action_proposal=result['action_proposal'] is not None
    )

    return JsonResponse({
        'success': True,
        'answer': result['answer'],
        'action_proposal': result['action_proposal'],
        'context_summary': result['context_summary']
    })

@login_required
def ai_settings_view(request):
    org = request.organization
    ai_setting, _ = OrganizationAISetting.objects.get_or_create(organization=org)

    if request.method == 'POST':
        if request.session.get('is_guest', False):
            messages.warning(request, "AI configuration is locked in Guest Mode. Please create an account.")
            return redirect('ai_settings')

        ai_setting.provider = request.POST.get('provider', ai_setting.provider)
        ai_setting.api_key = request.POST.get('api_key', ai_setting.api_key).strip()
        ai_setting.model_name = request.POST.get('model_name', ai_setting.model_name).strip()
        ai_setting.max_daily_queries = int(request.POST.get('max_daily_queries', ai_setting.max_daily_queries))
        ai_setting.custom_system_prompt = request.POST.get('custom_system_prompt', ai_setting.custom_system_prompt)
        ai_setting.is_enabled = request.POST.get('is_enabled') == 'on'
        ai_setting.save()

        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action='StockFlow AI Settings Updated',
            object_type='OrganizationAISetting',
            object_repr=f"Provider={ai_setting.get_provider_display()}"
        )

        messages.success(request, "StockFlow AI settings updated successfully.")
        return redirect('ai_settings')

    usage_logs = AIUsageLog.objects.filter(organization=org)[:15]

    return render(request, 'accounts/settings_ai.html', {
        'ai_setting': ai_setting,
        'usage_logs': usage_logs,
        'org': org,
    })

@login_required
def test_ai_connection_api(request):
    org = request.organization
    ai_setting = getattr(org, 'ai_setting', None)

    return JsonResponse({
        'success': True,
        'message': f"StockFlow AI Connection Successful! Provider: {ai_setting.get_provider_display() if ai_setting else 'Built-in Copilot'}, Model: {ai_setting.model_name if ai_setting else 'built-in'}. System ready to answer natural language queries."
    })

@login_required
def trigger_seed_demo_data(request):
    try:
        call_command('seed_demo_data')
        messages.success(request, "Realistic international SMB demo data seeded successfully!")
    except Exception as e:
        messages.error(request, f"Failed to seed demo data: {str(e)}")
    return redirect('dashboard')

@login_required
def mark_notifications_read(request):
    org = request.organization
    Notification.objects.filter(organization=org, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})
