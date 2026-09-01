import re

def render_template_vars(content, context_data):
    """
    Replaces both {{variable}} and {variable} placeholders with context values.
    """
    res = content
    for key, val in context_data.items():
        str_val = str(val) if val is not None else ""
        res = res.replace(f"{{{{{key}}}}}", str_val)
        res = res.replace(f"{{{key}}}", str_val)
    return res

def parse_sales_message(message_text, product_queryset, customer_name="Customer", conversation_messages=None, business=None):
    """
    Parses incoming customer product sales inquiry in Hinglish / Hindi / English with multi-turn context tracking
    and predefined SalesAgentTemplate matching.

    Pulls price and stock directly from Product model database objects — NEVER estimates or invents.

    Returns structured output dict:
    {
        'intent': 'product_interest' | 'price_question' | 'availability_check' | 'order_confirmation' | 'quantity_inquiry' | 'recommendation' | 'unclear',
        'template_type': str,
        'matched_product': Product model instance or None,
        'quantity': int,
        'unit_price': float or None,
        'total_amount': float or None,
        'auto_reply': str,
        'create_draft_order': bool,
        'needs_owner': bool,
        'summary': str
    }
    """
    text = message_text.lower().strip()

    result = {
        'intent': 'unclear',
        'template_type': 'general',
        'matched_product': None,
        'quantity': 1,
        'unit_price': None,
        'total_amount': None,
        'auto_reply': '',
        'create_draft_order': False,
        'needs_owner': False,
        'summary': ''
    }

    products = list(product_queryset)

    # 1. Match Product directly from current message_text
    best_product = None
    best_score = 0

    for prod in products:
        p_name = prod.name.lower().strip()
        if p_name in text:
            score = len(p_name) * 2
        else:
            tokens = [t for t in re.split(r'\W+', p_name) if len(t) > 2]
            score = sum(1 for t in tokens if t in text)
        
        if score > best_score and score >= 2:
            best_score = score
            best_product = prod

    # 2. Context-Based Product Resolution (if no direct product match in current text)
    context_used = False
    if not best_product and conversation_messages:
        for msg in reversed(list(conversation_messages)):
            m_text = msg.message_text.lower()
            for prod in products:
                p_name = prod.name.lower().strip()
                if p_name in m_text:
                    best_product = prod
                    context_used = True
                    break
            if best_product:
                break

    result['matched_product'] = best_product

    # 3. Extract Quantity if present
    has_explicit_quantity = False
    qty_match = re.search(r'(\d+)\s*(?:kg|g|pc|pcs|unit|units|pkt|packet|packets|box|boxes|bottle|bottles|tins)?', text)
    if qty_match:
        try:
            parsed_q = int(qty_match.group(1))
            if 1 <= parsed_q <= 1000:
                result['quantity'] = parsed_q
                has_explicit_quantity = True
        except ValueError:
            pass

    # 4. Detect Intent & Map to Template Type
    recommend_keywords = ['healthy', 'best', 'recommend', 'suggest', 'achha', 'options', 'kya achha hai', 'top', 'kuch naya']
    affirmative_keywords = ['haan', 'yes', 'chahiye', 'bhejo', 'pack', 'kar do', 'ok', 'ha', 'sure', 'bhej do', 'pack kar do', 'kar', 'dunge', 'hha']
    order_keywords = ['bhej do', 'pack kar do', 'order', 'chahiye', 'buy', 'kharidna', 'purchase', 'confirm', 'book kar do', 'lene hai', 'bhejo', 'packet']
    price_keywords = ['price', 'kitne ka', 'kitna', 'rate', 'cost', 'kya price', 'how much', 'daam', 'rs', 'rupee']
    stock_keywords = ['stock', 'available', 'hai kya', 'mil jayega', 'in stock', 'kya stock']
    welcome_keywords = ['hi', 'hello', 'namaste', 'hey', 'start', 'shuru']

    is_recommend = any(k in text for k in recommend_keywords)
    is_affirmation = any(k in text for k in affirmative_keywords)
    is_order_intent = any(k in text for k in order_keywords)

    if is_recommend:
        result['intent'] = 'recommendation'
        result['template_type'] = 'recommendation'
    elif is_order_intent or (is_affirmation and has_explicit_quantity):
        result['intent'] = 'order_confirmation'
        result['template_type'] = 'order_confirmation'
    elif is_affirmation and not has_explicit_quantity:
        result['intent'] = 'quantity_inquiry'
        result['template_type'] = 'customer_interested'
    elif any(k in text for k in price_keywords):
        result['intent'] = 'price_question'
        result['template_type'] = 'price_reply'
    elif any(k in text for k in stock_keywords):
        result['intent'] = 'availability_check'
        result['template_type'] = 'stock_reply'
    elif any(k in text for k in welcome_keywords):
        result['intent'] = 'welcome'
        result['template_type'] = 'welcome'
    elif best_product:
        result['intent'] = 'product_interest'
        result['template_type'] = 'product_inquiry'

    # Build Recommendations String
    in_stock_prods = [p for p in products if p.stock_quantity > 0]
    recommendations_list = [f"{p.name} (₹{p.selling_price:,.2f})" for p in in_stock_prods[:3]]
    recommendations_str = ", ".join(recommendations_list) if recommendations_list else "No active products in stock"

    # Context Data for Template Placeholders
    ctx = {
        'customer_name': customer_name,
        'product_name': best_product.name if best_product else "Product",
        'price': f"{best_product.selling_price:,.2f}" if best_product else "0.00",
        'stock': f"{best_product.stock_quantity}" if best_product else "0",
        'quantity': f"{result['quantity']}",
        'total_amount': f"{(float(best_product.selling_price) * result['quantity']):,.2f}" if best_product else "0.00",
        'recommendations': recommendations_str,
        'order_id': "Draft",
    }

    if best_product:
        result['unit_price'] = float(best_product.selling_price)
        result['total_amount'] = result['unit_price'] * result['quantity']

    # Template Lookup Function
    def get_active_template(msg_type):
        if business:
            from sales_agent.models import SalesAgentTemplate
            return SalesAgentTemplate.objects.filter(business=business, message_type=msg_type, is_active=True).first()
        return None

    # Handle Recommendation Intent
    if result['intent'] == 'recommendation':
        active_tpl = get_active_template('recommendation')
        if active_tpl:
            result['auto_reply'] = render_template_vars(active_tpl.content, ctx)
        else:
            result['auto_reply'] = f"Namaste {customer_name}! Aapke liye best available options: {recommendations_str}. Aap isme se koi bhi order kar sakte hain!"
        result['summary'] = f"Recommended top in-stock products: {recommendations_str}."
        return result

    # No Product Matched
    if not best_product:
        active_tpl = get_active_template('human_handoff') or get_active_template('general')
        if active_tpl:
            result['auto_reply'] = render_template_vars(active_tpl.content, ctx)
        else:
            result['auto_reply'] = f"Namaste {customer_name}! Aapka sales inquiry message receive ho gaya hai. Store owner jald hi aapko product availability and price ke saath contact karenge."
        result['needs_owner'] = True
        result['summary'] = "Unclear product match — handed over to store owner."
        return result

    # Out of Stock Handling
    if best_product.stock_quantity <= 0:
        result['needs_owner'] = True
        active_tpl = get_active_template('out_of_stock')
        if active_tpl:
            result['auto_reply'] = render_template_vars(active_tpl.content, ctx)
        else:
            result['auto_reply'] = f"Namaste {customer_name}! Maaf kijiyega, '{best_product.name}' abhi Out of Stock hai. Store owner restock hote hi aapko notify karenge."
        result['summary'] = f"Product '{best_product.name}' is out of stock. Handoff to owner."
        return result

    # Quantity Inquiry (Follow-up affirmation "Haan, chahiye")
    if result['intent'] == 'quantity_inquiry':
        active_tpl = get_active_template('customer_interested')
        if active_tpl:
            result['auto_reply'] = render_template_vars(active_tpl.content, ctx)
        else:
            result['auto_reply'] = (
                f"Ji bilkul {customer_name}! '{best_product.name}' (₹{best_product.selling_price:,.2f} per unit) "
                f"ke kitne packets / units chahiye? (e.g. 1 packet, 2 packets)"
            )
        result['summary'] = f"Acknowledged interest in '{best_product.name}' from context."
        return result

    # Order Confirmation ("2 packet kar do")
    if result['intent'] == 'order_confirmation' or (context_used and has_explicit_quantity):
        if result['quantity'] > best_product.stock_quantity:
            result['needs_owner'] = True
            result['auto_reply'] = f"Namaste {customer_name}! '{best_product.name}' ke sirf {best_product.stock_quantity} units stock me available hain. Store owner jald hi aapko contact karenge."
            result['summary'] = f"Requested quantity ({result['quantity']}) exceeds stock ({best_product.stock_quantity})."
            return result

        result['create_draft_order'] = True
        active_tpl = get_active_template('order_confirmation')
        if active_tpl:
            result['auto_reply'] = render_template_vars(active_tpl.content, ctx)
        else:
            result['auto_reply'] = (
                f"Namaste {customer_name}! Aapka order for {result['quantity']}x {best_product.name} "
                f"(Total: ₹{result['total_amount']:,.2f}) draft order me log ho gaya hai. "
                f"Store owner ki approval ke baad final confirmation message aayega! Dhanyawad."
            )
        result['summary'] = f"Draft order created for {result['quantity']}x {best_product.name} (Total: ₹{result['total_amount']:,.2f})."
        return result

    # Price / Availability / Product Inquiry
    active_tpl = get_active_template(result['template_type'])
    if active_tpl:
        result['auto_reply'] = render_template_vars(active_tpl.content, ctx)
    else:
        result['auto_reply'] = (
            f"Namaste {customer_name}! '{best_product.name}' ka price ₹{best_product.selling_price:,.2f} per unit hai. "
            f"Available Stock: {best_product.stock_quantity} units. "
            f"Kya aap isse order karna chahte hain? Reply karein (e.g. 'Haan, 2 packets')."
        )
    result['summary'] = f"Responded with database price ₹{best_product.selling_price:,.2f} and stock {best_product.stock_quantity}."
    return result
