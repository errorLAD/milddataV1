from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from apps.sales.models import Invoice, Customer, Payment, InvoiceStatus
from apps.inventory.models import Product, StockMovement, ProductType
from apps.purchasing.models import PurchaseOrder, Supplier, POStatus
from apps.finance.models import Expense, ExpenseCategory
from apps.people.models import Employee, Attendance, AttendanceStatus
from apps.core.models import UserRole

def check_permission(user_profile, required_permission):
    """
    Role permission checker.
    Owner/Admin/Manager have full access.
    Employee/Sales/Warehouse have restricted access (e.g. no salary info).
    """
    if not user_profile:
        return False
    role = user_profile.role
    if role in [UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER]:
        return True
    
    if required_permission == 'view_salary' and role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.ACCOUNTANT]:
        return False
    if required_permission == 'view_financials' and role in [UserRole.EMPLOYEE, UserRole.WAREHOUSE]:
        return False
    return True

def get_sales_summary(org, days=30):
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    prev_start_date = start_date - timedelta(days=days)
    
    current_invoices = Invoice.objects.filter(organization=org, date__gte=start_date, date__lte=today).exclude(status=InvoiceStatus.VOID)
    current_sales = current_invoices.aggregate(total=Sum('total_amount'))['total'] or 0.00
    
    prev_invoices = Invoice.objects.filter(organization=org, date__gte=prev_start_date, date__lt=start_date).exclude(status=InvoiceStatus.VOID)
    prev_sales = prev_invoices.aggregate(total=Sum('total_amount'))['total'] or 0.00
    
    growth = 0.0
    if prev_sales > 0:
        growth = round(((current_sales - prev_sales) / prev_sales) * 100, 1)
    
    return {
        'period_days': days,
        'current_sales': float(current_sales),
        'prev_sales': float(prev_sales),
        'growth_percent': growth,
        'invoice_count': current_invoices.count(),
        'currency': org.currency_symbol
    }

def get_inventory_status(org):
    products = Product.objects.filter(organization=org)
    total_products = products.count()
    physical_products = products.filter(product_type=ProductType.PHYSICAL)
    
    total_units = physical_products.aggregate(total=Sum('stock_quantity'))['total'] or 0
    inventory_value = sum(p.stock_quantity * p.purchase_price for p in physical_products)
    low_stock = [p for p in physical_products if p.is_low_stock and p.stock_quantity > 0]
    out_of_stock = [p for p in physical_products if p.stock_quantity <= 0]
    
    return {
        'total_products': total_products,
        'total_units': total_units,
        'inventory_value': float(inventory_value),
        'low_stock_count': len(low_stock),
        'out_of_stock_count': len(out_of_stock),
        'low_stock_products': [{'name': p.name, 'sku': p.sku, 'stock': p.stock_quantity, 'reorder': p.reorder_level} for p in low_stock[:5]],
        'out_of_stock_products': [{'name': p.name, 'sku': p.sku} for p in out_of_stock[:5]],
        'currency': org.currency_symbol
    }

def get_low_stock_products(org):
    products = Product.objects.filter(organization=org, product_type=ProductType.PHYSICAL)
    low_stock = [p for p in products if p.is_low_stock]
    return {
        'count': len(low_stock),
        'items': [{'name': p.name, 'sku': p.sku, 'stock': p.stock_quantity, 'reorder_level': p.reorder_level, 'price': float(p.purchase_price)} for p in low_stock],
        'currency': org.currency_symbol
    }

def get_overdue_invoices(org):
    today = timezone.now().date()
    overdue = Invoice.objects.filter(organization=org, due_date__lt=today).exclude(status__in=[InvoiceStatus.PAID, InvoiceStatus.VOID])
    total_overdue = sum(inv.remaining_amount for inv in overdue)
    
    items = []
    for inv in overdue:
        items.append({
            'invoice_number': inv.invoice_number,
            'customer': inv.customer.company_name,
            'due_date': str(inv.due_date),
            'remaining_amount': float(inv.remaining_amount),
            'total_amount': float(inv.total_amount)
        })
        
    return {
        'count': len(items),
        'total_amount': float(total_overdue),
        'items': items,
        'currency': org.currency_symbol
    }

def get_customer_balance(org, customer_name=None):
    customers = Customer.objects.filter(organization=org)
    if customer_name:
        customers = customers.filter(company_name__icontains=customer_name)
    
    results = []
    total_outstanding = 0.0
    for cust in customers:
        invoices = Invoice.objects.filter(customer=cust).exclude(status__in=[InvoiceStatus.PAID, InvoiceStatus.VOID])
        bal = sum(inv.remaining_amount for inv in invoices)
        if bal > 0 or customer_name:
            results.append({
                'customer_name': cust.company_name,
                'outstanding': float(bal),
                'email': cust.email
            })
            total_outstanding += float(bal)
            
    return {
        'total_outstanding': total_outstanding,
        'customer_count': len(results),
        'customers': sorted(results, key=lambda x: x['outstanding'], reverse=True),
        'currency': org.currency_symbol
    }

def get_top_customers(org, limit=5):
    today = timezone.now().date()
    start_of_year = datetime(today.year, 1, 1).date()
    
    invoices = Invoice.objects.filter(organization=org, date__gte=start_of_year).exclude(status=InvoiceStatus.VOID)
    cust_totals = {}
    for inv in invoices:
        name = inv.customer.company_name
        cust_totals[name] = cust_totals.get(name, 0.0) + float(inv.total_amount)
        
    sorted_custs = sorted(cust_totals.items(), key=lambda x: x[1], reverse=True)[:limit]
    return {
        'year': today.year,
        'top_customers': [{'name': name, 'purchased_amount': amount} for name, amount in sorted_custs],
        'currency': org.currency_symbol
    }

def get_expense_summary(org, days=30):
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    expenses = Expense.objects.filter(organization=org, date__gte=start_date)
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0.00
    
    # Category breakdown
    cat_totals = {}
    for exp in expenses:
        cat_name = exp.category.name if exp.category else 'General'
        cat_totals[cat_name] = cat_totals.get(cat_name, 0.0) + float(exp.amount)
        
    sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
    return {
        'period_days': days,
        'total_expenses': float(total_expenses),
        'categories': [{'category': cat, 'amount': amt} for cat, amt in sorted_cats],
        'top_expense': sorted_cats[0] if sorted_cats else ('None', 0.0),
        'currency': org.currency_symbol
    }

def get_employee_attendance(org, target_date=None):
    if not target_date:
        target_date = timezone.now().date()
    
    total_employees = Employee.objects.filter(organization=org, status='ACTIVE').count()
    records = Attendance.objects.filter(organization=org, date=target_date)
    
    present = records.filter(status__in=[AttendanceStatus.PRESENT, AttendanceStatus.REMOTE, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]).count()
    absent = records.filter(status=AttendanceStatus.ABSENT).count()
    absent_employees = [r.employee.name for r in records.filter(status=AttendanceStatus.ABSENT)]
    
    return {
        'date': str(target_date),
        'total_employees': total_employees,
        'present_count': present,
        'absent_count': absent,
        'absent_employees': absent_employees
    }

def get_profit_summary(org, days=30):
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    
    invoices = Invoice.objects.filter(organization=org, date__gte=start_date).exclude(status=InvoiceStatus.VOID)
    revenue = float(invoices.aggregate(total=Sum('total_amount'))['total'] or 0.00)
    
    expenses = Expense.objects.filter(organization=org, date__gte=start_date)
    total_expenses = float(expenses.aggregate(total=Sum('amount'))['total'] or 0.00)
    
    pos = PurchaseOrder.objects.filter(organization=org, date__gte=start_date).exclude(status=POStatus.CANCELLED)
    cogs = float(pos.aggregate(total=Sum('total_amount'))['total'] or 0.00)
    
    gross_profit = revenue - cogs
    net_profit = gross_profit - total_expenses
    
    return {
        'period_days': days,
        'revenue': revenue,
        'cogs': cogs,
        'expenses': total_expenses,
        'gross_profit': gross_profit,
        'estimated_net_profit': net_profit,
        'currency': org.currency_symbol
    }
