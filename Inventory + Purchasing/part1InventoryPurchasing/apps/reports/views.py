from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from decimal import Decimal
import csv
import datetime

from apps.sales.models import Invoice, Customer
from apps.purchasing.models import PurchaseOrder, Supplier
from apps.inventory.models import Product, StockMovement, Warehouse

@login_required
def reports_index_view(request):
    org = request.organization
    report_type = request.GET.get('type', 'sales')

    # Date range filters
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    data = []

    if report_type == 'sales':
        invoices = Invoice.objects.filter(organization=org).exclude(status='VOID')
        if start_date:
            invoices = invoices.filter(invoice_date__gte=start_date)
        if end_date:
            invoices = invoices.filter(invoice_date__lte=end_date)
        data = invoices

    elif report_type == 'purchases':
        pos = PurchaseOrder.objects.filter(organization=org).exclude(status='CANCELLED')
        if start_date:
            pos = pos.filter(order_date__gte=start_date)
        if end_date:
            pos = pos.filter(order_date__lte=end_date)
        data = pos

    elif report_type == 'inventory':
        products = Product.objects.filter(organization=org, is_archived=False)
        data = products

    elif report_type == 'movements':
        movements = StockMovement.objects.filter(organization=org)
        if start_date:
            movements = movements.filter(created_at__date__gte=start_date)
        if end_date:
            movements = movements.filter(created_at__date__lte=end_date)
        data = movements[:200]

    elif report_type == 'customers':
        customers = Customer.objects.filter(organization=org)
        data = customers

    elif report_type == 'suppliers':
        suppliers = Supplier.objects.filter(organization=org)
        data = suppliers

    context = {
        'report_type': report_type,
        'data': data,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'reports/reports_index.html', context)

@login_required
def export_report_csv(request):
    org = request.organization
    report_type = request.GET.get('type', 'sales')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="stockflow_{report_type}_report.csv"'

    writer = csv.writer(response)

    if report_type == 'sales':
        writer.writerow(['Invoice Number', 'Customer', 'Date', 'Due Date', 'Status', 'Subtotal', 'Tax', 'Total Amount', 'Paid Amount', 'Balance'])
        invoices = Invoice.objects.filter(organization=org).exclude(status='VOID')
        for inv in invoices:
            writer.writerow([inv.invoice_number, inv.customer.company_name, inv.invoice_date, inv.due_date, inv.get_status_display(), inv.subtotal, inv.tax_amount, inv.total_amount, inv.paid_amount, inv.remaining_balance])

    elif report_type == 'purchases':
        writer.writerow(['PO Number', 'Supplier', 'Order Date', 'Status', 'Subtotal', 'Tax', 'Total Amount'])
        pos = PurchaseOrder.objects.filter(organization=org).exclude(status='CANCELLED')
        for po in pos:
            writer.writerow([po.po_number, po.supplier.company_name, po.order_date, po.get_status_display(), po.subtotal, po.tax_amount, po.total_amount])

    elif report_type == 'inventory':
        writer.writerow(['Product Name', 'SKU', 'Barcode', 'Category', 'Unit', 'Purchase Price', 'Selling Price', 'Total Stock', 'Inventory Value', 'Status'])
        products = Product.objects.filter(organization=org, is_archived=False)
        for p in products:
            cat_name = p.category.name if p.category else 'N/A'
            unit_name = p.unit.abbreviation if p.unit else 'pcs'
            writer.writerow([p.name, p.sku, p.barcode, cat_name, unit_name, p.purchase_price, p.selling_price, p.total_stock, p.inventory_value, p.status])

    elif report_type == 'movements':
        writer.writerow(['Date', 'Product', 'SKU', 'Warehouse', 'Movement Type', 'Quantity', 'Reference', 'User'])
        movements = StockMovement.objects.filter(organization=org)[:500]
        for m in movements:
            u = m.user.username if m.user else 'System'
            writer.writerow([m.created_at.strftime('%Y-%m-%d %H:%M'), m.product.name, m.product.sku, m.warehouse.code, m.get_movement_type_display(), m.quantity, m.reference, u])

    elif report_type == 'customers':
        writer.writerow(['Company Name', 'Contact Person', 'Email', 'Phone', 'Country', 'Total Sales', 'Outstanding Balance'])
        for c in Customer.objects.filter(organization=org):
            writer.writerow([c.company_name, c.contact_person, c.email, c.phone, c.country, c.total_sales, c.outstanding_balance])

    elif report_type == 'suppliers':
        writer.writerow(['Company Name', 'Contact Person', 'Email', 'Phone', 'Country', 'Total Purchases', 'Outstanding Payables'])
        for s in Supplier.objects.filter(organization=org):
            writer.writerow([s.company_name, s.contact_person, s.email, s.phone, s.country, s.total_purchases, s.outstanding_payables])

    return response
