import datetime
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, Q

from sales.models import Sale, SaleItem
from udhaar.models import Udhaar
from products.models import Product
from customers.models import Customer
from payments.models import Payment
from whatsapp.models import WhatsAppConversation, WhatsAppMessage

def get_date_bounds(period_code, custom_start=None, custom_end=None):
    today = timezone.now().date()
    
    if period_code == '7_days':
        start = today - datetime.timedelta(days=7)
        end = today
    elif period_code == '90_days':
        start = today - datetime.timedelta(days=90)
        end = today
    elif period_code == 'this_month':
        start = today.replace(day=1)
        end = today
    elif period_code == 'previous_month':
        first_of_this_month = today.replace(day=1)
        end = first_of_this_month - datetime.timedelta(days=1)
        start = end.replace(day=1)
    elif period_code == 'this_year':
        start = today.replace(month=1, day=1)
        end = today
    elif period_code == 'custom' and custom_start and custom_end:
        start = custom_start
        end = custom_end
    else:
        # Default: 30_days
        start = today - datetime.timedelta(days=30)
        end = today
        
    return start, end

def get_business_health_summary(business, start_date, end_date):
    from suppliers.models import Supplier, SupplierPurchase
    sales_qs = Sale.objects.filter(business=business, sale_date__date__range=[start_date, end_date])
    total_sales = sales_qs.aggregate(s=Sum('total_amount'))['s'] or 0
    
    udhaar_qs = Udhaar.objects.filter(business=business).exclude(status='Paid')
    total_udhaar = udhaar_qs.aggregate(s=Sum('remaining_amount'))['s'] or 0
    
    overdue_qs = udhaar_qs.filter(status='Overdue')
    overdue_amount = overdue_qs.aggregate(s=Sum('remaining_amount'))['s'] or 0

    supplier_purchases = SupplierPurchase.objects.filter(business=business).exclude(status='Paid')
    total_supplier_payable = sum([p.remaining_payable for p in supplier_purchases])
    overdue_supplier_payable = sum([p.remaining_payable for p in supplier_purchases.filter(status='Overdue')])

    if sales_qs.count() == 0 and udhaar_qs.count() == 0 and supplier_purchases.count() == 0:
        return {
            'status': 'Insufficient Data',
            'status_color': 'secondary',
            'summary': 'Not enough data to make this recommendation. Start logging sales, products, customer udhaar, and supplier purchases to activate AI insights.',
            'total_sales': 0.0,
            'total_udhaar': 0.0,
            'overdue_amount': 0.0,
            'overdue_pct': 0.0,
            'total_supplier_payable': 0.0
        }

    overdue_pct = round((float(overdue_amount) / float(total_udhaar) * 100), 1) if total_udhaar > 0 else 0
    slow_prods = Product.objects.filter(business=business, stock_quantity__gt=10).count()

    if overdue_pct > 35 or overdue_amount > 50000 or overdue_supplier_payable > 40000:
        status = 'Critical Risk'
        status_color = 'danger'
    elif overdue_pct > 15 or slow_prods > 3 or total_supplier_payable > total_udhaar:
        status = 'Needs Attention'
        status_color = 'warning'
    else:
        status = 'Healthy'
        status_color = 'success'

    top_overdue_custs = overdue_qs.order_by('-remaining_amount')[:3]
    top_cust_names = ", ".join([u.customer.name for u in top_overdue_custs]) if top_overdue_custs.exists() else "None"

    summary_text = (
        f"Sales revenue is ₹{total_sales:,.2f} for the selected period, with ₹{total_udhaar:,.2f} in Customer Receivables and ₹{total_supplier_payable:,.2f} in Supplier Payables. "
        f"{overdue_pct}% of customer receivable (₹{overdue_amount:,.2f}) is overdue. "
    )
    if top_overdue_custs.exists():
        summary_text += f"Key overdue customer accounts: {top_cust_names}. "
    if overdue_supplier_payable > 0:
        summary_text += f"Attention: ₹{overdue_supplier_payable:,.2f} in supplier payables is currently past due date."

    return {
        'status': status,
        'status_color': status_color,
        'summary': summary_text,
        'total_sales': float(total_sales),
        'total_udhaar': float(total_udhaar),
        'overdue_amount': float(overdue_amount),
        'overdue_pct': overdue_pct,
        'total_supplier_payable': float(total_supplier_payable),
        'overdue_supplier_payable': float(overdue_supplier_payable)
    }

def get_supplier_payable_insights(business):
    from suppliers.models import Supplier, SupplierPurchase
    active_purchases = SupplierPurchase.objects.filter(business=business).exclude(status='Paid')
    total_payable = sum([p.remaining_payable for p in active_purchases])
    overdue_payable = sum([p.remaining_payable for p in active_purchases.filter(status='Overdue')])

    today = timezone.now().date()
    due_today_cnt = active_purchases.filter(due_date=today).count()
    due_soon_cnt = active_purchases.filter(due_date__gt=today, due_date__lte=today + datetime.timedelta(days=7)).count()

    # Top Suppliers Owed
    top_suppliers_qs = Supplier.objects.filter(business=business)
    top_suppliers = []
    for s in top_suppliers_qs:
        if s.outstanding_payable > 0:
            top_suppliers.append({
                'supplier_id': s.id,
                'supplier_name': s.supplier_name,
                'phone': s.phone,
                'outstanding_payable': s.outstanding_payable,
                'overdue_payable': s.overdue_payable
            })
    top_suppliers.sort(key=lambda x: x['outstanding_payable'], reverse=True)

    return {
        'total_payable': float(total_payable),
        'overdue_payable': float(overdue_payable),
        'due_today_cnt': due_today_cnt,
        'due_soon_cnt': due_soon_cnt,
        'top_suppliers_owed': top_suppliers[:5]
    }

def get_udhaar_recovery_insights(business, start_date, end_date):
    udhaars = Udhaar.objects.filter(business=business)
    active_udhaars = udhaars.exclude(status='Paid')
    
    total_outstanding = active_udhaars.aggregate(s=Sum('remaining_amount'))['s'] or 0
    overdue_udhaars = active_udhaars.filter(status='Overdue')
    total_overdue = overdue_udhaars.aggregate(s=Sum('remaining_amount'))['s'] or 0

    today = timezone.now().date()
    due_today_cnt = active_udhaars.filter(due_date=today).count()
    due_today_amt = active_udhaars.filter(due_date=today).aggregate(s=Sum('remaining_amount'))['s'] or 0

    due_soon_cnt = active_udhaars.filter(due_date__gt=today, due_date__lte=today + datetime.timedelta(days=7)).count()
    due_soon_amt = active_udhaars.filter(due_date__gt=today, due_date__lte=today + datetime.timedelta(days=7)).aggregate(s=Sum('remaining_amount'))['s'] or 0

    broken_promises_cnt = active_udhaars.filter(promise_broken=True).count()

    problems = []

    # Problem 1: Concentrated Overdue Amount
    if total_overdue > 0:
        top_overdue = overdue_udhaars.order_by('-remaining_amount')[:4]
        top_amt = sum([u.remaining_amount for u in top_overdue])
        conc_pct = round((float(top_amt) / float(total_overdue) * 100), 1)
        cust_cnt = top_overdue.count()

        problems.append({
            'title': f"₹{total_overdue:,.2f} Overdue Credit Concentration",
            'problem': f"₹{top_amt:,.2f} of overdue money is concentrated in just {cust_cnt} customer account(s).",
            'evidence': f"Data shows {cust_cnt} customer(s) account for {conc_pct}% of total overdue udhaar.",
            'reason': "These customers have repeatedly delayed payments or broken promised payment dates.",
            'action': f"Prioritize manual follow-up with these {cust_cnt} customers and pause extending additional credit until previous balances are reduced.",
            'priority': 'High' if conc_pct > 50 else 'Medium'
        })

    # Problem 2: High Broken Promises
    if broken_promises_cnt > 0:
        problems.append({
            'title': f"{broken_promises_cnt} Payment Promises Broken",
            'problem': f"{broken_promises_cnt} customer(s) agreed on payment dates but failed to pay on time.",
            'evidence': f"Database tracks {broken_promises_cnt} broken promise flags across active udhaars.",
            'reason': "Automated reminders were sent, but payments were not recorded by promised dates.",
            'action': "Contact these customers directly via phone or WhatsApp with direct payment links.",
            'priority': 'High'
        })

    return {
        'total_outstanding': float(total_outstanding),
        'total_overdue': float(total_overdue),
        'due_today_cnt': due_today_cnt,
        'due_today_amt': float(due_today_amt),
        'due_soon_cnt': due_soon_cnt,
        'due_soon_amt': float(due_soon_amt),
        'broken_promises_cnt': broken_promises_cnt,
        'problems': problems
    }

def get_customer_payment_risks(business):
    customers = Customer.objects.filter(business=business)
    
    risks = []
    for c in customers:
        active_u = c.udhaars.exclude(status='Paid')
        out_amt = active_u.aggregate(s=Sum('remaining_amount'))['s'] or 0
        
        if out_amt <= 0 and c.sales.count() < 2:
            tier = 'Insufficient Data'
            tier_badge = 'secondary'
            reason = "Limited purchase and payment history."
            action = "Monitor initial credit limits."
        else:
            overdue_u = active_u.filter(status='Overdue')
            max_days_overdue = max([u.days_overdue for u in overdue_u]) if overdue_u.exists() else 0
            broken_cnt = active_u.filter(promise_broken=True).count()
            
            if max_days_overdue > 15 or broken_cnt >= 2 or (out_amt > 20000 and max_days_overdue > 7):
                tier = 'High Risk'
                tier_badge = 'danger'
                reason = f"Overdue by {max_days_overdue} days with {broken_cnt} broken payment promise(s)."
                action = "Follow up manually before extending additional credit."
            elif max_days_overdue > 0 or broken_cnt == 1 or out_amt > 10000:
                tier = 'Medium Risk'
                tier_badge = 'warning'
                reason = f"Outstanding balance ₹{out_amt:,.2f} with minor payment delay."
                action = "Send polite payment reminder and verify payment link."
            else:
                tier = 'Low Risk'
                tier_badge = 'success'
                reason = "Consistent payment history with prompt settlements."
                action = "Eligible for standard credit terms."

        risks.append({
            'customer_id': c.id,
            'customer_name': c.name,
            'customer_phone': c.phone,
            'outstanding': float(out_amt),
            'days_overdue': max([u.days_overdue for u in active_u]) if active_u.exists() else 0,
            'broken_promises': active_u.filter(promise_broken=True).count() if active_u.exists() else 0,
            'risk_tier': tier,
            'tier_badge': tier_badge,
            'reason': reason,
            'action': action
        })

    risks.sort(key=lambda x: (x['risk_tier'] != 'High Risk', -x['outstanding']))
    return risks

def get_todays_priority_contacts(business):
    today = timezone.now().date()
    active_udhaars = Udhaar.objects.filter(business=business).exclude(status='Paid')
    
    priorities = []
    for u in active_udhaars:
        score = 0
        if u.status == 'Overdue':
            score += 50 + min(u.days_overdue, 30)
        if u.promise_broken:
            score += 40
        if u.promised_date and u.promised_date <= today:
            score += 30
        score += min(int(u.remaining_amount / 1000), 30)

        recommended = "Follow up today regarding balance."
        if u.promise_broken:
            recommended = "Payment promise was broken. Call or message today."
        elif u.status == 'Overdue':
            recommended = f"Balance overdue by {u.days_overdue} days. Send reminder with payment link."

        priorities.append({
            'score': score,
            'udhaar_id': u.id,
            'customer_id': u.customer.id,
            'customer_name': u.customer.name,
            'customer_phone': u.customer.phone,
            'outstanding': float(u.remaining_amount),
            'days_overdue': u.days_overdue,
            'promised_date': u.promised_date.strftime('%Y-%m-%d') if u.promised_date else None,
            'recommended_action': recommended
        })

    priorities.sort(key=lambda x: x['score'], reverse=True)
    return priorities[:5]

def get_sales_velocity_and_slow_inventory(business, start_date, end_date):
    items = SaleItem.objects.filter(sale__business=business, sale__sale_date__date__range=[start_date, end_date])
    
    # Fast Moving Products
    fast_items = items.values('product_name').annotate(
        total_units=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_units')[:5]

    fast_moving = []
    for fi in fast_items:
        fast_moving.append({
            'product_name': fi['product_name'],
            'units_sold': fi['total_units'],
            'revenue': float(fi['total_revenue'])
        })

    # Slow Moving Products
    all_products = Product.objects.filter(business=business)
    slow_moving = []
    
    for p in all_products:
        sold_in_period = items.filter(product=p).aggregate(u=Sum('quantity'))['u'] or 0
        if p.stock_quantity > 5 and sold_in_period <= 2:
            slow_moving.append({
                'product_id': p.id,
                'product_name': p.name,
                'stock': p.stock_quantity,
                'sold_in_period': sold_in_period,
                'recommendation': "Avoid purchasing additional stock until existing inventory moves."
            })

    slow_moving.sort(key=lambda x: x['stock'], reverse=True)
    return {
        'fast_moving': fast_moving,
        'slow_moving': slow_moving[:5]
    }

def get_restock_recommendations(business):
    products = Product.objects.filter(business=business)
    restock_list = []
    
    for p in products:
        if p.stock_quantity <= p.low_stock_threshold or p.stock_quantity <= 5:
            restock_list.append({
                'product_id': p.id,
                'product_name': p.name,
                'current_stock': p.stock_quantity,
                'low_stock_threshold': p.low_stock_threshold,
                'recommendation': f"Current stock ({p.stock_quantity}) is low. Consider restocking soon."
            })
            
    restock_list.sort(key=lambda x: x['current_stock'])
    return restock_list[:5]

def get_product_profitability(business, start_date, end_date):
    items = SaleItem.objects.filter(sale__business=business, sale__sale_date__date__range=[start_date, end_date])
    
    prods = Product.objects.filter(business=business)
    insights = []
    
    for p in prods:
        p_items = items.filter(product=p)
        units_sold = p_items.aggregate(u=Sum('quantity'))['u'] or 0
        revenue = p_items.aggregate(r=Sum('subtotal'))['r'] or 0
        
        if p.cost_price and p.cost_price > 0 and p.selling_price > 0:
            unit_margin = float(p.selling_price - p.cost_price)
            margin_pct = round((unit_margin / float(p.selling_price) * 100), 1)
            est_profit = unit_margin * units_sold
        else:
            margin_pct = 0.0
            est_profit = 0.0

        insights.append({
            'product_id': p.id,
            'product_name': p.name,
            'units_sold': units_sold,
            'revenue': float(revenue),
            'margin_pct': margin_pct,
            'est_profit': float(est_profit)
        })

    insights.sort(key=lambda x: x['revenue'], reverse=True)
    return insights[:10]

def get_customer_sales_behavior(business, start_date, end_date):
    sales = Sale.objects.filter(business=business, sale_date__date__range=[start_date, end_date])
    
    top_customers = sales.values('customer__name').annotate(
        total_spent=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('-total_spent')[:5]

    res = []
    for tc in top_customers:
        res.append({
            'customer_name': tc['customer__name'],
            'total_spent': float(tc['total_spent'] or 0),
            'order_count': tc['order_count']
        })

    return {
        'top_customers': res
    }

def get_todays_top_actions(business):
    actions = []
    
    # 1. High Overdue Udhaars
    overdue_u = Udhaar.objects.filter(business=business, status='Overdue').order_by('-remaining_amount').first()
    if overdue_u:
        actions.append({
            'title': f"Recover ₹{overdue_u.remaining_amount:,.2f} from {overdue_u.customer.name}",
            'detail': f"Balance is overdue by {overdue_u.days_overdue} days.",
            'action_text': 'View Customer',
            'link_url': f"/customers/{overdue_u.customer.pk}/",
            'icon': 'bi-telephone-outbound',
            'btn_class': 'btn-danger'
        })

    # 2. Broken Promise Follow-up
    broken_u = Udhaar.objects.filter(business=business, promise_broken=True).first()
    if broken_u:
        actions.append({
            'title': f"Follow up with {broken_u.customer.name}",
            'detail': f"Promised payment on {broken_u.promised_date.strftime('%d %b') if broken_u.promised_date else 'recent date'} was not received.",
            'action_text': 'Send WhatsApp',
            'link_url': "/whatsapp/inbox/",
            'icon': 'bi-whatsapp',
            'btn_class': 'btn-success'
        })

    # 3. Restock Low Inventory
    low_p = Product.objects.filter(business=business, stock_quantity__lte=5).first()
    if low_p:
        actions.append({
            'title': f"Restock '{low_p.name}'",
            'detail': f"Current stock is down to {low_p.stock_quantity} units.",
            'action_text': 'View Product',
            'link_url': f"/products/{low_p.pk}/edit/",
            'icon': 'bi-box-seam',
            'btn_class': 'btn-primary'
        })

    # 4. Record Pending Payments
    pending_pay_u = Udhaar.objects.filter(business=business, verification_status='Payment Claimed').first()
    if pending_pay_u:
        actions.append({
            'title': f"Verify Payment Claim for {pending_pay_u.customer.name}",
            'detail': f"Customer claimed payment for ₹{pending_pay_u.remaining_amount:,.2f}.",
            'action_text': 'Record Payment',
            'link_url': f"/udhaar/{pending_pay_u.pk}/",
            'icon': 'bi-check-circle',
            'btn_class': 'btn-warning'
        })

    # 5. Review Draft Sales Orders
    from sales_agent.models import DraftOrder
    pending_draft = DraftOrder.objects.filter(business=business, status='Pending Owner Confirmation').first()
    if pending_draft:
        actions.append({
            'title': f"Approve AI Draft Order: {pending_draft.customer.name}",
            'detail': f"Requested {pending_draft.quantity}x {pending_draft.product.name if pending_draft.product else 'Item'} (₹{pending_draft.total_amount:,.2f}).",
            'action_text': 'View Sales Agent',
            'link_url': "/sales-agent/",
            'icon': 'bi-robot',
            'btn_class': 'btn-info'
        })

    return actions[:5]

def build_structured_analytics_payload(business, start_date, end_date):
    health = get_business_health_summary(business, start_date, end_date)
    udhaar = get_udhaar_recovery_insights(business, start_date, end_date)
    suppliers_payload = get_supplier_payable_insights(business)
    risks = get_customer_payment_risks(business)
    priority_contacts = get_todays_priority_contacts(business)
    velocity = get_sales_velocity_and_slow_inventory(business, start_date, end_date)
    restock = get_restock_recommendations(business)
    profitability = get_product_profitability(business, start_date, end_date)
    customer_behavior = get_customer_sales_behavior(business, start_date, end_date)
    top_actions = get_todays_top_actions(business)

    return {
        'period_start': start_date.strftime('%Y-%m-%d'),
        'period_end': end_date.strftime('%Y-%m-%d'),
        'business_health': health,
        'udhaar_summary': udhaar,
        'supplier_payables': suppliers_payload,
        'customer_risks': risks[:10],
        'priority_contacts': priority_contacts,
        'fast_moving_products': velocity['fast_moving'],
        'slow_moving_products': velocity['slow_moving'],
        'restock_recommendations': restock,
        'product_profitability': profitability,
        'top_customers': customer_behavior['top_customers'],
        'todays_top_actions': top_actions
    }
