import re
import datetime
from django.utils import timezone

def parse_customer_message(message_text):
    """
    Parses incoming customer WhatsApp message text in Hindi / Hinglish / English.
    Returns structured data dictionary:
    {
        'intent': 'promise' | 'ready_to_pay' | 'paid_claimed' | 'dispute' | 'wrong_number' | 'need_time' | 'unknown',
        'promised_date': date object or None,
        'promised_amount': float or None,
        'dispute_flag': bool,
        'wrong_number_flag': bool,
        'summary': str
    }
    """
    text = message_text.lower().strip()
    today = timezone.now().date()

    result = {
        'intent': 'unknown',
        'promised_date': None,
        'promised_amount': None,
        'dispute_flag': False,
        'wrong_number_flag': False,
        'summary': ''
    }

    # 1. Check Wrong Number Intent
    if any(k in text for k in ['wrong number', 'galat number', 'number galat', 'kon ho', 'who is this', 'galat h']):
        result['intent'] = 'wrong_number'
        result['wrong_number_flag'] = True
        result['summary'] = 'Customer claims wrong phone number.'
        return result

    # 2. Check Dispute Intent
    if any(k in text for k in ['galat hai', 'amount galat', 'galat account', 'wrong amount', 'dispute', 'mismatch', 'itna nahi', 'hisaab galat']):
        result['intent'] = 'dispute'
        result['dispute_flag'] = True
        result['summary'] = 'Customer disputed the balance or invoice amount.'
        return result

    # 3. Check Payment Claimed Intent ("Maine payment kar diya")
    if any(k in text for k in ['payment kar diya', 'paid', 'pay kar diya', 'bhej diya', 'sent payment', 'done payment', 'transfer kar diya', 'chuka diya']):
        result['intent'] = 'paid_claimed'
        result['summary'] = 'Customer claims payment has been made.'
        return result

    # 4. Check Ready to Pay / Send UPI Intent ("UPI bhejo")
    if any(k in text for k in ['upi bhejo', 'send upi', 'qr bhejo', 'send qr', 'payment link', 'link bhejo', 'pay karta hu', 'pay kar rha hu', 'how to pay', 'kahan pay karu']):
        result['intent'] = 'ready_to_pay'
        result['summary'] = 'Customer is ready to pay and requested payment link/UPI.'
        return result

    # 5. Check Promise Intent ("Kal de dunga", "Friday ko 5000 dunga")
    promise_keywords = ['dunga', 'denge', 'dungi', 'pay karunga', 'de dunga', 'bhej dunga', 'bhej dungi', 'promise', 'takk', 'par dunga']
    if any(k in text for k in promise_keywords) or 'kal' in text or 'parso' in text:
        result['intent'] = 'promise'
        
        # Extract Date
        if 'kal' in text or 'tomorrow' in text:
            result['promised_date'] = today + datetime.timedelta(days=1)
        elif 'parso' in text:
            result['promised_date'] = today + datetime.timedelta(days=2)
        elif 'aaj' in text or 'today' in text:
            result['promised_date'] = today
        else:
            # Check day names (e.g. Friday, Monday)
            days = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6,
                    'somwar': 0, 'mangalwar': 1, 'budhwar': 2, 'guruwar': 3, 'shukrawar': 4, 'shaniwar': 5, 'raviwar': 6}
            for d_name, d_idx in days.items():
                if d_name in text:
                    current_idx = today.weekday()
                    days_ahead = (d_idx - current_idx + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    result['promised_date'] = today + datetime.timedelta(days=days_ahead)
                    break
            
            if not result['promised_date']:
                # Default promise = tomorrow
                result['promised_date'] = today + datetime.timedelta(days=1)

        # Extract Amount (Regex for numbers like 5000, 20,000, 5k)
        amt_match = re.search(r'(?:rs\.?|₹|\b)(\d[\d,]*)(?:k\b|\b)', text)
        if amt_match:
            try:
                num_str = amt_match.group(1).replace(',', '')
                val = float(num_str)
                if 'k' in text[amt_match.end():amt_match.end()+2]:
                    val *= 1000
                result['promised_amount'] = val
            except ValueError:
                pass

        p_date_str = result['promised_date'].strftime('%d %b %Y') if result['promised_date'] else 'Soon'
        result['summary'] = f"Customer promised payment on {p_date_str}."
        return result

    # 6. Check Need Time Intent ("Abhi paise nahi hain")
    if any(k in text for k in ['paise nahi', 'no money', 'salary', 'samay', 'time chahiye', 'paisa nahi', 'funds nahi']):
        result['intent'] = 'need_time'
        result['promised_date'] = today + datetime.timedelta(days=5) # Default 5 days grace
        result['summary'] = 'Customer requested more time to arrange funds.'
        return result

    return result
