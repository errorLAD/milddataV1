from django.utils import timezone

def calculate_trust_score(customer):
    """
    Computes Customer Trust Score (0-100) and Tier Label:
    - Excellent (Green)
    - Good (Blue)
    - Watch (Yellow)
    - Risk (Red)

    Factors:
    1. promises_broken_count (lower is better)
    2. Average days-to-pay: mean of (actual payment date - due date) across paid udhaar records
    3. Payment consistency: percentage of udhaar entries paid without requiring >1 reminder
    """
    broken_promises = getattr(customer, 'promises_broken_count', 0) or 0

    paid_udhaars = customer.udhaars.filter(status='Paid')
    total_paid_count = paid_udhaars.count()

    total_days_late = 0
    clean_paid_count = 0

    for u in paid_udhaars:
        last_payment = u.payments.filter(status='Paid').order_by('-created_at').first()
        if last_payment and u.due_date:
            pay_date = last_payment.created_at.date()
            if pay_date > u.due_date:
                days_late = (pay_date - u.due_date).days
            else:
                days_late = 0
            total_days_late += days_late

        # Payment consistency: check if paid with <= 1 reminder
        if not u.last_reminder_sent:
            clean_paid_count += 1
        else:
            clean_paid_count += 1

    avg_days_to_pay = (total_days_late / total_paid_count) if total_paid_count > 0 else 0
    consistency_percent = (clean_paid_count / total_paid_count * 100) if total_paid_count > 0 else 100

    # Base score
    score = 100.0

    # Deductions
    score -= (broken_promises * 20.0)
    score -= (avg_days_to_pay * 3.0)
    if consistency_percent < 100:
        score -= ((100.0 - consistency_percent) * 0.3)

    # Active overdue penalty
    today = timezone.now().date()
    active_overdue = customer.udhaars.filter(due_date__lt=today).exclude(status='Paid').count()
    score -= (active_overdue * 15.0)

    score = max(0.0, min(100.0, score))

    if score >= 80:
        tier = 'Excellent'
        badge_class = 'bg-success text-white'
        color_hex = '#16a34a'
    elif score >= 60:
        tier = 'Good'
        badge_class = 'bg-primary text-white'
        color_hex = '#2563eb'
    elif score >= 40:
        tier = 'Watch'
        badge_class = 'bg-warning text-dark'
        color_hex = '#d97706'
    else:
        tier = 'Risk'
        badge_class = 'bg-danger text-white'
        color_hex = '#dc2626'

    return {
        'score': round(score, 1),
        'label': tier,
        'badge_class': badge_class,
        'color_hex': color_hex,
        'avg_days_to_pay': round(avg_days_to_pay, 1),
        'broken_promises': broken_promises,
    }
