import re
from apps.core.ai_tools import (
    check_permission, get_sales_summary, get_inventory_status, get_low_stock_products,
    get_overdue_invoices, get_customer_balance, get_top_customers,
    get_expense_summary, get_employee_attendance, get_profit_summary
)
from apps.sales.models import Customer, Product
from apps.purchasing.models import Supplier

def process_ai_request(query, user_profile, organization):
    if not query or not query.strip():
        return {
            'text': "How can I help you today? You can ask about sales, stock, overdue invoices, expenses, top customers, or profit.",
            'action': None,
            'link': None
        }

    q = query.strip().lower()

    # Permission check for salary queries
    if 'salary' in q or 'pay' in q or 'payroll' in q:
        if not check_permission(user_profile, 'view_salary'):
            return {
                'text': "🔒 You do not have permission to view salary and compensation information.",
                'action': None,
                'link': None
            }

    # Action Preparation 1: Draft Invoice
    if 'create invoice' in q or 'draft invoice' in q or 'make invoice' in q:
        # Extract customer and product if present
        customer_match = re.search(r'for\s+([A-Za-z0-9\s]+?)(?=\s+for|\s+with|\s*$)', query, re.IGNORECASE)
        cust_name = customer_match.group(1).strip() if customer_match else "Select Customer"
        
        c_obj = Customer.objects.filter(organization=organization, company_name__icontains=cust_name).first()
        p_obj = Product.objects.filter(organization=organization).first()
        
        return {
            'text': f"I prepared an invoice draft for **{c_obj.company_name if c_obj else cust_name}**. Please review and confirm before saving.",
            'action': {
                'type': 'DRAFT_INVOICE',
                'title': 'Review Invoice Draft',
                'customer_id': c_obj.id if c_obj else '',
                'customer_name': c_obj.company_name if c_obj else cust_name,
                'product_id': p_obj.id if p_obj else '',
                'product_name': p_obj.name if p_obj else 'Product',
                'unit_price': float(p_obj.selling_price) if p_obj else 100.0,
                'quantity': 10
            },
            'link': {'label': 'Review Invoice', 'url': '/sales/invoices/create/'}
        }

    # Action Preparation 2: Draft Purchase Order
    if 'create purchase' in q or 'create po' in q or 'draft purchase' in q:
        supp_match = re.search(r'from\s+([A-Za-z0-9\s]+?)(?=\s+for|\s+with|\s*$)', query, re.IGNORECASE)
        supp_name = supp_match.group(1).strip() if supp_match else "Select Supplier"
        
        s_obj = Supplier.objects.filter(organization=organization, company_name__icontains=supp_name).first()
        p_obj = Product.objects.filter(organization=organization).first()

        return {
            'text': f"I prepared a purchase order draft for **{s_obj.company_name if s_obj else supp_name}**. Please review and confirm before saving.",
            'action': {
                'type': 'DRAFT_PO',
                'title': 'Review Purchase Order Draft',
                'supplier_id': s_obj.id if s_obj else '',
                'supplier_name': s_obj.company_name if s_obj else supp_name,
                'product_id': p_obj.id if p_obj else '',
                'product_name': p_obj.name if p_obj else 'Product',
                'unit_cost': float(p_obj.purchase_price) if p_obj else 50.0,
                'quantity': 50
            },
            'link': {'label': 'Review Purchase Order', 'url': '/purchasing/orders/create/'}
        }

    # Q&A 1: Sales
    if any(k in q for k in ['sell', 'sales', 'revenue', 'sales performance']):
        data = get_sales_summary(organization, days=30)
        growth_str = f"+{data['growth_percent']}%" if data['growth_percent'] >= 0 else f"{data['growth_percent']}%"
        return {
            'text': f"Your sales this month are **{data['currency']}{data['current_sales']:,.2f}** ({growth_str} compared to previous 30 days) across **{data['invoice_count']} invoices**.",
            'action': None,
            'link': {'label': 'View Invoices', 'url': '/sales/invoices/'}
        }

    # Q&A 2: Low Stock & Reordering
    if any(k in q for k in ['low stock', 'reorder', 'out of stock', 'products need reordering']):
        data = get_low_stock_products(organization)
        if data['count'] == 0:
            return {
                'text': "✅ All products are currently above their reorder level. No immediate stock warnings.",
                'action': None,
                'link': {'label': 'View Inventory', 'url': '/inventory/products/'}
            }
        
        top_items = ", ".join([f"**{item['name']}** ({item['stock']} left)" for item in data['items'][:3]])
        return {
            'text': f"⚠️ **{data['count']} products** are below their reorder level. Most urgent items: {top_items}.",
            'action': None,
            'link': {'label': 'View Low Stock Products', 'url': '/inventory/products/?filter=low_stock'}
        }

    # Q&A 3: Overdue & Who owes money
    if any(k in q for k in ['owes me', 'who owes', 'overdue', 'unpaid', 'receivables']):
        data = get_overdue_invoices(organization)
        if data['count'] == 0:
            return {
                'text': "🎉 Great news! You have no overdue invoices right now.",
                'action': None,
                'link': {'label': 'View Receivables', 'url': '/finance/receivables/'}
            }
        return {
            'text': f"⚠️ **{data['count']} customers** have overdue invoices totaling **{data['currency']}{data['total_amount']:,.2f}**.",
            'action': None,
            'link': {'label': 'View Overdue Invoices', 'url': '/finance/receivables/'}
        }

    # Q&A 4: Biggest Expenses
    if any(k in q for k in ['expense', 'biggest expense', 'spending', 'costs']):
        data = get_expense_summary(organization, days=30)
        top_cats = "\n".join([f"• **{cat['category']}**: {data['currency']}{cat['amount']:,.2f}" for cat in data['categories'][:4]])
        return {
            'text': f"Your total expenses this month are **{data['currency']}{data['total_expenses']:,.2f}**.\n\nLargest expense categories:\n{top_cats if top_cats else 'No expenses recorded.'}",
            'action': None,
            'link': {'label': 'View Expenses', 'url': '/finance/expenses/'}
        }

    # Q&A 5: Top Customer
    if any(k in q for k in ['bought the most', 'top customer', 'best customer', 'biggest customer']):
        data = get_top_customers(organization, limit=5)
        if not data['top_customers']:
            return {
                'text': "No customer sales recorded yet this year.",
                'action': None,
                'link': {'label': 'View Customers', 'url': '/sales/customers/'}
            }
        top = data['top_customers'][0]
        return {
            'text': f"🏆 **{top['name']}** purchased the most this year with **{data['currency']}{top['purchased_amount']:,.2f}** in orders.",
            'action': None,
            'link': {'label': 'View Customers', 'url': '/sales/customers/'}
        }

    # Q&A 6: Profit
    if any(k in q for k in ['profit', 'how much profit', 'net profit', 'gross profit', 'earnings']):
        data = get_profit_summary(organization, days=30)
        return {
            'text': f"Over the last 30 days:\n• Revenue: **{data['currency']}{data['revenue']:,.2f}**\n• COGS: **{data['currency']}{data['cogs']:,.2f}**\n• Expenses: **{data['currency']}{data['expenses']:,.2f}**\n• **Estimated Net Profit: {data['currency']}{data['estimated_net_profit']:,.2f}**",
            'action': None,
            'link': {'label': 'View Profit & Loss', 'url': '/finance/profit/'}
        }

    # Q&A 7: Attendance
    if any(k in q for k in ['attendance', 'absent', 'who is absent']):
        data = get_employee_attendance(organization)
        absent_str = ", ".join(data['absent_employees']) if data['absent_employees'] else "None"
        return {
            'text': f"Today's attendance status:\n• Present: **{data['present_count']}** / {data['total_employees']}\n• Absent: **{data['absent_count']}** ({absent_str})",
            'action': None,
            'link': {'label': 'View Attendance', 'url': '/people/attendance/'}
        }

    # Fallback response with suggested questions
    return {
        'text': f"I analyzed your company data for '{query}'. Here is a summary overview:\n• Active Customers: {Customer.objects.filter(organization=organization).count()}\n• Total Products: {Product.objects.filter(organization=organization).count()}\n\nTry asking:\n• *How are sales performing?*\n• *Which products need reordering?*\n• *Who owes me money?*\n• *What were my biggest expenses?*",
        'action': None,
        'link': {'label': 'Explore Reports', 'url': '/reports/'}
    }
