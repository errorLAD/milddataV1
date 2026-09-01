import requests
import json
from decimal import Decimal
import datetime
from django.db.models import Sum, Q

from apps.accounts.models import Organization
from apps.inventory.models import Product, Warehouse, Inventory, StockMovement
from apps.purchasing.models import Supplier, PurchaseOrder, PurchaseBill
from apps.sales.models import Customer, Invoice, SalesQuote
from apps.core.templatetags.locale_tags import money_format

class StockFlowAIEngine:
    def __init__(self, organization, user):
        self.org = organization
        self.user = user

    def get_realtime_context(self):
        """Builds a structured real-time snapshot of the company's DB state."""
        products = Product.objects.filter(organization=self.org, is_archived=False)
        invoices = Invoice.objects.filter(organization=self.org).exclude(status='VOID')
        open_invoices = invoices.filter(status__in=['UNPAID', 'PARTIALLY_PAID', 'OVERDUE'])
        open_bills = PurchaseBill.objects.filter(organization=self.org, status__in=['OPEN', 'PARTIALLY_PAID', 'OVERDUE'])

        low_stock_items = [
            f"{p.name} (SKU: {p.sku}, Stock: {p.total_stock}, Reorder Threshold: {p.reorder_level})"
            for p in products if p.product_type == 'PHYSICAL' and p.total_stock <= p.reorder_level
        ]

        debtors = [
            f"{inv.customer.company_name}: {money_format(inv.remaining_balance, self.org)} (Inv {inv.invoice_number}, Due: {inv.due_date})"
            for inv in open_invoices
        ]

        creditors = [
            f"{bill.supplier.company_name}: {money_format(bill.remaining_balance, self.org)} (Bill {bill.bill_number}, Due: {bill.due_date})"
            for bill in open_bills
        ]

        total_sales_val = sum(inv.total_amount for inv in invoices)
        total_inv_val = sum(p.inventory_value for p in products if p.product_type == 'PHYSICAL')
        total_ar_val = sum(inv.remaining_balance for inv in open_invoices)
        total_ap_val = sum(bill.remaining_balance for bill in open_bills)

        return {
            'company_name': self.org.name,
            'currency': self.org.currency_code,
            'tax_name': self.org.tax_name,
            'low_stock_items': low_stock_items,
            'debtors': debtors[:10],
            'creditors': creditors[:10],
            'total_sales_val': money_format(total_sales_val, self.org),
            'total_inv_val': money_format(total_inv_val, self.org),
            'total_ar_val': money_format(total_ar_val, self.org),
            'total_ap_val': money_format(total_ap_val, self.org),
            'product_count': products.count(),
            'customer_count': Customer.objects.filter(organization=self.org).count(),
            'supplier_count': Supplier.objects.filter(organization=self.org).count(),
        }

    def process_query(self, prompt):
        q = prompt.strip().lower()
        context = self.get_realtime_context()
        action_proposal = None

        # 1. Action Intent Detection (Human-in-the-Loop Safeguard)
        if 'reorder' in q or 'purchase order' in q or 'buy' in q:
            low_item = context['low_stock_items'][0] if context['low_stock_items'] else 'Wireless Router'
            action_proposal = {
                'title': 'Create Purchase Order for Low Stock Restock',
                'description': f'Draft a Purchase Order to restock low items: {low_item}',
                'action_url': '/purchasing/pos/create/',
                'type': 'create_po'
            }
        elif 'invoice' in q or 'bill customer' in q:
            action_proposal = {
                'title': 'Create New Sales Invoice',
                'description': 'Generate a commercial sales invoice for a customer',
                'action_url': '/sales/invoices/create/',
                'type': 'create_invoice'
            }

        # 2. Natural Language Answering based on real DB Context
        if 'low' in q or 'stock' in q or 'reorder' in q:
            if context['low_stock_items']:
                items_str = "\n• " + "\n• ".join(context['low_stock_items'])
                answer = f"Here are the items currently low or out of stock in {context['company_name']}:{items_str}\n\nTotal Inventory Value: {context['total_inv_val']} across {context['product_count']} products."
            else:
                answer = f"Good news! All {context['product_count']} products in {context['company_name']} are currently adequately stocked above reorder thresholds."

        elif 'owes' in q or 'receivable' in q or 'debt' in q or 'unpaid' in q:
            if context['debtors']:
                debt_str = "\n• " + "\n• ".join(context['debtors'])
                answer = f"Total Outstanding Receivables: {context['total_ar_val']}.\n\nCustomers with unpaid invoices:{debt_str}"
            else:
                answer = f"You currently have zero outstanding receivables! All customer invoices are paid in full."

        elif 'payable' in q or 'supplier' in q or 'owe' in q:
            if context['creditors']:
                cred_str = "\n• " + "\n• ".join(context['creditors'])
                answer = f"Total Outstanding Payables: {context['total_ap_val']}.\n\nSuppliers awaiting payment:{cred_str}"
            else:
                answer = f"You have no pending supplier payables."

        elif 'sales' in q or 'revenue' in q or 'performance' in q:
            answer = f"Summary for {context['company_name']}:\n• Total Sales Volume: {context['total_sales_val']}\n• Total Inventory Value: {context['total_inv_val']}\n• Active Customers: {context['customer_count']}\n• Active Suppliers: {context['supplier_count']}"

        else:
            answer = f"StockFlow AI Overview for {context['company_name']}:\n" \
                     f"• Total Inventory Value: {context['total_inv_val']} ({context['product_count']} items)\n" \
                     f"• Outstanding Receivables: {context['total_ar_val']}\n" \
                     f"• Outstanding Payables: {context['total_ap_val']}\n" \
                     f"• Low Stock Alerts: {len(context['low_stock_items'])} products requiring restock.\n\n" \
                     f"Ask me about low stock items, unpaid receivables, supplier payables, or specific product SKU details!"

        return {
            'answer': answer,
            'action_proposal': action_proposal,
            'context_summary': f"Computed live from {context['company_name']} database."
        }
