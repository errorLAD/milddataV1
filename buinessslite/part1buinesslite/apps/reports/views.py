from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
import csv

from apps.sales.models import Invoice, SalesOrder, Customer
from apps.inventory.models import Product, StockMovement
from apps.purchasing.models import PurchaseOrder, Supplier
from apps.finance.models import Expense
from apps.people.models import Attendance, Employee

@login_required
def reports_dashboard_view(request):
    org = request.organization
    report_type = request.GET.get('type', 'sales')
    
    context = {
        'report_type': report_type,
        'customers': Customer.objects.filter(organization=org),
        'suppliers': Supplier.objects.filter(organization=org),
        'products': Product.objects.filter(organization=org),
        'employees': Employee.objects.filter(organization=org),
    }

    if report_type == 'sales':
        invoices = Invoice.objects.filter(organization=org)
        context['invoices'] = invoices
    elif report_type == 'purchases':
        orders = PurchaseOrder.objects.filter(organization=org)
        context['orders'] = orders
    elif report_type == 'inventory':
        products = Product.objects.filter(organization=org)
        context['products'] = products
    elif report_type == 'expenses':
        expenses = Expense.objects.filter(organization=org)
        context['expenses'] = expenses

    return render(request, 'reports/dashboard.html', context)

@login_required
def export_csv_view(request, report_type):
    org = request.organization
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="businesslite_{report_type}_report.csv"'
    writer = csv.writer(response)

    if report_type == 'sales':
        writer.writerow(['Invoice #', 'Customer', 'Date', 'Due Date', 'Status', 'Total', 'Paid', 'Remaining'])
        for inv in Invoice.objects.filter(organization=org):
            writer.writerow([inv.invoice_number, inv.customer.company_name, inv.date, inv.due_date, inv.status, inv.total_amount, inv.paid_amount, inv.remaining_amount])
    
    elif report_type == 'inventory':
        writer.writerow(['Product', 'SKU', 'Type', 'Category', 'Selling Price', 'Cost Price', 'Stock Quantity', 'Low Stock'])
        for p in Product.objects.filter(organization=org):
            writer.writerow([p.name, p.sku, p.product_type, p.category.name if p.category else '', p.selling_price, p.purchase_price, p.stock_quantity, 'YES' if p.is_low_stock else 'NO'])

    elif report_type == 'expenses':
        writer.writerow(['Title', 'Category', 'Vendor', 'Date', 'Payment Method', 'Amount'])
        for exp in Expense.objects.filter(organization=org):
            writer.writerow([exp.title, exp.category.name if exp.category else '', exp.vendor, exp.date, exp.payment_method, exp.amount])

    elif report_type == 'purchases':
        writer.writerow(['PO #', 'Supplier', 'Date', 'Expected Delivery', 'Status', 'Total'])
        for po in PurchaseOrder.objects.filter(organization=org):
            writer.writerow([po.po_number, po.supplier.company_name, po.date, po.expected_delivery, po.status, po.total_amount])

    elif report_type == 'salaries':
        writer.writerow(['Date', 'Employee', 'Payout Type', 'Payment Mode', 'Reference', 'Amount Paid'])
        from apps.people.models import SalaryPayment
        for sp in SalaryPayment.objects.filter(organization=org):
            writer.writerow([sp.payment_date, sp.employee.name, sp.payout_type, sp.payment_mode, sp.reference_number, sp.amount])

    return response
